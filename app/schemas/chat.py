from typing import Optional

from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    user_id: str
    conversation_id: str