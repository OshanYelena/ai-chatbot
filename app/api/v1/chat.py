from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.services.long_term_memory import long_term_memory_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.core.logger import setup_logger



router = APIRouter(prefix="/chat", tags=["Chat"])
logger = setup_logger(__name__)


@router.post("/", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    trace_id = request.state.trace_id

    try:
        repo = ConversationRepository(db)

        conversation_id = memory_service.get_or_create_conversation(
            repo=repo,
            conversation_id=payload.conversation_id,
        )

        logger.info(
            f"Chat request received | trace_id={trace_id} | conversation_id={conversation_id}"
        )

        memory_service.add_message(
            repo=repo,
            conversation_id=conversation_id,
            role="user",
            content=payload.message,
        )

        extracted_facts = llm_service.extract_user_facts(payload.message)

        for key, value in extracted_facts.items():
            long_term_memory_service.update_memory(
                repo=repo,
                conversation_id=conversation_id,
                key=key,
                value=value,
            )

        context_messages = memory_service.build_context_messages(
            repo=repo,
            conversation_id=conversation_id,
        )

        reply = llm_service.generate_reply(context_messages)

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

            summary = llm_service.summarize_messages(full_messages)

            memory_service.compress_conversation(
                repo=repo,
                conversation_id=conversation_id,
                summary=summary,
            )

        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
        )

    except Exception:
        logger.exception(f"Chat request failed | trace_id={trace_id}")
        raise HTTPException(
            status_code=500,
            detail="Chat service failed. Please try again.",
        )