from typing import List, Optional, Any, Type
from sqlalchemy.orm import Session

from app.db.models import Conversation, ChatMessage, LongTermMemory


class ConversationRepository:
    def __init__(self, db:Session):
        self.db = db

    def get_conversation(self, conversation_id) -> set[Type[Conversation]]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()

        )
    def create_conversation(self) -> Conversation:
        conversation = Conversation()
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_or_create_conversation(self, conversation_id: Optional[str]) -> Conversation:
        if conversation_id:
            conversation = self.get_conversation(conversation_id)
            if conversation:
                return conversation

        return self.create_conversation()


    def add_message(self, conversation_id: str, role:str, content:str) -> ChatMessage:
        message = ChatMessage(

            conversation_id=conversation_id,

            role=role,

            content=content,

        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages(self, conversation_id: str) -> List[ChatMessage]:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .all()

        )

    def get_recent_messages(self, conversation_id: str, limit: int) -> List[ChatMessage]:
        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()

        )
        return list(reversed(messages))

    def get_message_count(self, conversation_id: str) -> int:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .count()
        )

    def get_summary(self, conversation_id: str) -> str:
        conversation = self.get_conversation(conversation_id)
        return conversation.summary if conversation and conversation.summary else ""

    def update_summary(self, conversation_id: str, summary: str):
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return
        conversation.summary = summary
        self.db.commit()
        self.db.refresh(conversation)

    def compress_conversation(self, conversation_id: str, keep_last: int):
        recent_messages = self.get_recent_messages(conversation_id, keep_last)
        self.db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id

        ).delete()
        self.db.commit()
        for message in recent_messages:
            new_message = ChatMessage(
                conversation_id=conversation_id,
                role=message.role,
                content=message.content,
            )
            self.db.add(new_message)
        self.db.commit()

    def upsert_long_term_memory(self, conversation_id: str, key: str, value: str):
        memory = (
            self.db.query(LongTermMemory)
            .filter(
                LongTermMemory.conversation_id == conversation_id,
                LongTermMemory.key == key,
            )
            .first()
        )
        if memory:
            memory.value = str(value)
        else:
            memory = LongTermMemory(
                conversation_id=conversation_id,
                key=key,
                value=str(value),
            )
            self.db.add(memory)

        self.db.commit()