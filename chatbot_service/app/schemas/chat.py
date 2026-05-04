from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    # user_id is NO LONGER supplied by the client —
    # it is extracted from the verified JWT by the verify_token dependency
    # and injected into the endpoint. This schema is kept for the message
    # and optional conversation_id only.
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    user_id: str
    conversation_id: str
