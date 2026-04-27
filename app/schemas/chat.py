from typing import Optional

from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id:Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str