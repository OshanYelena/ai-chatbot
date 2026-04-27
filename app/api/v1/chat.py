from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):

    conversation_id = memory_service.get_or_create_conversation(
        request.conversation_id
    )

    memory_service.add_message(
        conversation_id,
        role="user",
        content=request.message
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