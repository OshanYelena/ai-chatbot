from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply = llm_service.generate_reply(request.message)
    return ChatResponse(reply=reply)