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

    messages = memory_service.get_messages(conversation_id)

    reply = llm_service.generate_reply(messages)
    return ChatResponse(reply=reply, conversation_id=conversation_id)