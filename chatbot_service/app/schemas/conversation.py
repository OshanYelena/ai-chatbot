from datetime import datetime
from typing import Optional

from pydantic import BaseModel



class ConversationListItem(BaseModel):
    conversation_id: str
    summary: Optional[str]
    created_at: datetime
    last_activity_at: datetime
    last_message: Optional[str]


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    conversation_id: str
    summary: Optional[str]
    messages: list[MessageItem]