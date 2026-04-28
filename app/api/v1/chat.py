from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.logger import setup_logger
from app.core.rate_limiter import limiter
from app.db.database import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.services.long_term_memory import long_term_memory_service

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = setup_logger(__name__)


@router.post("/", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(get_db),
):
    trace_id = request.state.trace_id

    try:
        repo = ConversationRepository(db)

        conversation_id = memory_service.get_or_create_conversation(
            repo=repo,
            user_id=payload.user_id,
            conversation_id=payload.conversation_id,
        )

        logger.info(
            "chat_request",
            extra={
                "trace_id": trace_id,
                "conversation_id": conversation_id,
                "user_id": payload.user_id,
                "event": "chat_request",
            },
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

        for key, value in extracted_facts.items():
            long_term_memory_service.update_memory(
                repo=repo,
                user_id=payload.user_id,
                key=key,
                value=value,
            )

        context_messages = memory_service.build_context_messages(
            repo=repo,
            user_id=payload.user_id,
            conversation_id=conversation_id,
        )

        reply = llm_service.generate_reply(
            context_messages,
            trace_id,
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

        return ChatResponse(
            reply=reply,
            user_id=payload.user_id,
            conversation_id=conversation_id,
        )

    except Exception:
        logger.exception(
            "chat_failed",
            extra={
                "trace_id": trace_id,
                "user_id": payload.user_id,
                "event": "chat_failed",
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Chat service failed. Please try again.",
        )