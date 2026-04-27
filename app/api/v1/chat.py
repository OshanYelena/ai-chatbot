from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    return ChatResponse(
        reply=f"You said: {request.message}"
    )