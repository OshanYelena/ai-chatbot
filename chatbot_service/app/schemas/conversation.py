from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ConversationListItem(BaseModel):
    conversation_id: str
    summary: Optional[str]
    created_at: datetime
    last_activity_at: datetime
    last_message: Optional[str]