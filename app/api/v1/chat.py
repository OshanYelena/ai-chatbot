from fastapi import APIRouter, HTTPException

from app.services.long_term_memory import long_term_memory_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
 try:
    conversation_id = memory_service.get_or_create_conversation(
        request.conversation_id
    )

    logger.info(f"Chat request received | conversation_id={conversation_id}")

    memory_service.add_message(
        conversation_id,
        role="user",
        content=request.message
    )

    extracted_facts = llm_service.extract_user_facts(request.message)

    for key, value in extracted_facts.items():
        long_term_memory_service.update_memory(
            conversation_id,
            key,
            value
        )

    context_messages = memory_service.build_context_messages(conversation_id)

    reply = llm_service.generate_reply(context_messages)

    memory_service.add_message(
        conversation_id,
        role="assistant",
        content=reply
    )

    if memory_service.should_summarize(conversation_id):
        full_messages = memory_service.get_messages(conversation_id)
        summary = llm_service.summarize_messages(full_messages)
        memory_service.compress_conversation(conversation_id, summary)



    return ChatResponse(reply=reply, conversation_id=conversation_id)
 except Exception as e:
     logger.exception("chat request failed")
     raise HTTPException(
         status_code=500,
         detail="Chat service failed. Please try again.",

     )
