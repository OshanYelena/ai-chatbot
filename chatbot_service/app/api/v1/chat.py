from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import asyncio

from app.core.logger import setup_logger
from app.core.rate_limiter import limiter
from app.db.database import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.services.long_term_memory import long_term_memory_service
from app.services.pending_memory_service import pending_memory_service
from app.services.confirmation_service import confirmation_service
from app.services.eval_service import eval_service
from app.services.jwt_verifier import verify_token  # ← auth dependency

from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = setup_logger(__name__)


@router.post("/", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(
    request: Request,
    payload: ChatRequest,
    user_id: str = Depends(verify_token),   # ← identity from JWT, not request body
    db: Session = Depends(get_db),
):
    trace_id = request.state.trace_id

    try:
        repo = ConversationRepository(db)

        repo.expire_old_pending_memory_conflicts()

        conversation_id = memory_service.get_or_create_conversation(
            repo=repo,
            user_id=user_id,
            conversation_id=payload.conversation_id,
        )

        logger.info(
            "chat_request",
            extra={
                "trace_id": trace_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "event": "chat_request",
            },
        )

        pending_conflicts = pending_memory_service.get_pending_conflicts(
            repo=repo,
            conversation_id=conversation_id,
        )

        if pending_conflicts:

            decision = confirmation_service.quick_confirm(payload.message)

            if decision is None:
                decision = llm_service.detect_memory_confirmation(
                    payload.message,
                    trace_id,
                )

            eval_service.evaluate_confirmation_classification(
                repo=repo,
                classification=decision,
                trace_id=trace_id,
                user_id=user_id,
                conversation_id=conversation_id,
            )

            if decision == "confirm":

                updates = []

                for conflict in pending_conflicts:
                    result = long_term_memory_service.force_update_memory(
                        repo=repo,
                        user_id=user_id,
                        key=conflict["key"],
                        value=conflict["new_value"],
                    )
                    updates.append(result)

                pending_memory_service.clear_pending_conflicts(
                    repo=repo,
                    conversation_id=conversation_id,
                    status="confirmed",
                )

                reply = "Got it — I updated that memory."

                memory_service.add_message(
                    repo=repo,
                    conversation_id=conversation_id,
                    role="user",
                    content=payload.message,
                )

                memory_service.add_message(
                    repo=repo,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=reply,
                )
                db.commit()
                return ChatResponse(
                    reply=reply,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )

            if decision == "reject":
                pending_memory_service.clear_pending_conflicts(
                    repo=repo,
                    conversation_id=conversation_id,
                    status="rejected",
                )

                reply = "Got it — I kept the existing memory unchanged."

                memory_service.add_message(
                    repo=repo,
                    conversation_id=conversation_id,
                    role="user",
                    content=payload.message,
                )

                memory_service.add_message(
                    repo=repo,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=reply,
                )
                db.commit()
                return ChatResponse(
                    reply=reply,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )

        memory_service.add_message(
            repo=repo,
            conversation_id=conversation_id,
            role="user",
            content=payload.message,
        )

        extracted_facts = llm_service.extract_user_facts(
            payload.message,
            trace_id,
        )

        eval_service.evaluate_memory_extraction(
            repo=repo,
            extracted_facts=extracted_facts,
            trace_id=trace_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        memory_update_results = []

        for key, value in extracted_facts.items():
            result = long_term_memory_service.update_memory(
                repo=repo,
                user_id=user_id,
                key=key,
                value=value,
            )
            memory_update_results.append(result)

        memory_conflicts = [
            result for result in memory_update_results
            if result.get("status") == "conflict"
        ]

        if memory_conflicts:
            pending_memory_service.set_pending_conflicts(
                repo=repo,
                user_id=user_id,
                conversation_id=conversation_id,
                conflicts=memory_conflicts,
            )

        context_messages = memory_service.build_context_messages(
            repo=repo,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        if memory_conflicts:
            conflict_items = "\n".join(
                [
                    f"- {conflict['key']}: {conflict['old_value']} → {conflict['new_value']}"
                    for conflict in memory_conflicts
                ]
            )

            context_messages.insert(
                0,
                {
                    "role": "system",
                    "content": (
                        "Memory conflicts detected:\n"
                        f"{conflict_items}\n\n"
                        "Do not assume the new claims are true yet. "
                        "Ask the user one short yes/no question asking whether all these memory updates should be applied."
                    ),
                },
            )

        reply = llm_service.generate_reply(
            context_messages,
            trace_id,
        )

        eval_service.evaluate_response(
            repo=repo,
            reply=reply,
            trace_id=trace_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        memory_service.add_message(
            repo=repo,
            conversation_id=conversation_id,
            role="assistant",
            content=reply,
        )

        if memory_service.should_summarize(
            repo=repo,
            conversation_id=conversation_id,
        ):
            full_messages = memory_service.get_messages(
                repo=repo,
                conversation_id=conversation_id,
            )

            summary = llm_service.summarize_messages(
                full_messages,
                trace_id,
            )

            memory_service.compress_conversation(
                repo=repo,
                conversation_id=conversation_id,
                summary=summary,
            )
        db.commit()

        return ChatResponse(
            reply=reply,
            user_id=user_id,
            conversation_id=conversation_id,
        )

    except Exception as e:
        db.rollback()
        logger.exception(
            "chat_failed",
            extra={
                "trace_id": trace_id,
                "user_id": user_id,
                "conversation_id": payload.conversation_id,
                "event": "chat_failed",
                "error_message": str(e),
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Chat service failed. Please try again.",
        )


@router.post("/stream")
@limiter.limit("10/minute")
def chat_stream(
    request: Request,
    payload: ChatRequest,
    user_id: str = Depends(verify_token),   # ← identity from JWT
    db: Session = Depends(get_db),
):
    trace_id = request.state.trace_id

    try:
        repo = ConversationRepository(db)

        repo.expire_old_pending_memory_conflicts()

        conversation_id = memory_service.get_or_create_conversation(
            repo=repo,
            user_id=user_id,
            conversation_id=payload.conversation_id,
        )

        memory_service.add_message(
            repo=repo,
            conversation_id=conversation_id,
            role="user",
            content=payload.message,
        )

        extracted_facts = llm_service.extract_user_facts(
            payload.message,
            trace_id,
        )

        eval_service.evaluate_memory_extraction(
            repo=repo,
            extracted_facts=extracted_facts,
            trace_id=trace_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        memory_update_results = []

        for key, value in extracted_facts.items():
            result = long_term_memory_service.update_memory(
                repo=repo,
                user_id=user_id,
                key=key,
                value=value,
            )
            memory_update_results.append(result)

        memory_conflicts = [
            result for result in memory_update_results
            if result.get("status") == "conflict"
        ]

        if memory_conflicts:
            pending_memory_service.set_pending_conflicts(
                repo=repo,
                user_id=user_id,
                conversation_id=conversation_id,
                conflicts=memory_conflicts,
            )

        context_messages = memory_service.build_context_messages(
            repo=repo,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        if memory_conflicts:
            conflict_items = "\n".join(
                [
                    f"- {c['key']}: {c['old_value']} → {c['new_value']}"
                    for c in memory_conflicts
                ]
            )

            context_messages.insert(
                0,
                {
                    "role": "system",
                    "content": (
                        "Memory conflicts detected:\n"
                        f"{conflict_items}\n\n"
                        "Do not assume the new claims are true yet. "
                        "Ask the user one short yes/no question asking whether all these memory updates should be applied."
                    ),
                },
            )

        async def event_generator():
            full_reply = ""
            stream_completed = False

            try:
                for chunk in llm_service.stream_reply(
                    context_messages,
                    trace_id,
                ):
                    if await request.is_disconnected():
                        raise Exception("Client disconnected during stream")

                    full_reply += chunk
                    yield f"event: token\ndata: {chunk}\n\n"

                    await asyncio.sleep(0)

                stream_completed = True

                memory_service.add_message(
                    repo=repo,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_reply,
                )

                eval_service.evaluate_response(
                    repo=repo,
                    reply=full_reply,
                    trace_id=trace_id,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    operation="stream_reply",
                )

                db.commit()

                yield f"event: done\ndata: {conversation_id}\n\n"

            except Exception as e:
                db.rollback()

                logger.exception(
                    "chat_stream_failed_during_generation",
                    extra={
                        "trace_id": trace_id,
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "event": "chat_stream_failed_during_generation",
                        "error_message": str(e),
                        "partial_reply_length": len(full_reply),
                        "stream_completed": stream_completed,
                    },
                )

                yield "event: error\ndata: Streaming failed\n\n"

            finally:
                db.close()

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "X-Conversation-ID": conversation_id,
                "X-Trace-ID": trace_id,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        db.rollback()

        logger.exception(
            "chat_stream_failed",
            extra={
                "trace_id": trace_id,
                "user_id": user_id,
                "conversation_id": payload.conversation_id,
                "event": "chat_stream_failed",
                "error_message": str(e),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Chat streaming service failed. Please try again.",
        )
