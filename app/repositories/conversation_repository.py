from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.models import User, Conversation, ChatMessage, LongTermMemory
from app.db.models import PendingMemoryConflict


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------- User ----------

    def get_user(self, user_id: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def get_or_create_user(self, user_id: str) -> User:
        user = self.get_user(user_id)

        if user:
            return user

        user = User(id=user_id)
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    # ---------- Conversation ----------

    def get_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> Optional[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )

    def create_conversation(self, user_id: str) -> Conversation:
        self.get_or_create_user(user_id)

        conversation = Conversation(user_id=user_id)
        self.db.add(conversation)
        self.db.flush()
        self.db.refresh(conversation)
        return conversation

    def get_or_create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str],
    ) -> Conversation:
        self.get_or_create_user(user_id)

        if conversation_id:
            conversation = self.get_conversation(user_id, conversation_id)
            if conversation:
                return conversation

        return self.create_conversation(user_id)

    # ---------- Messages ----------

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> ChatMessage:
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.db.add(message)
        self.db.flush()
        self.db.refresh(message)
        return message

    def get_messages(self, conversation_id: str) -> List[ChatMessage]:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    def get_recent_messages(
        self,
        conversation_id: str,
        limit: int,
    ) -> List[ChatMessage]:
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

    # ---------- Summary ----------

    def get_summary(self, conversation_id: str) -> str:
        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        return conversation.summary if conversation and conversation.summary else ""

    def update_summary(self, conversation_id: str, summary: str):
        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            return

        conversation.summary = summary
        self.db.flush()
        self.db.refresh(conversation)

    def compress_conversation(self, conversation_id: str, keep_last: int):
        recent_messages = self.get_recent_messages(conversation_id, keep_last)

        self.db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).delete()

        self.db.flush()

        for message in recent_messages:
            new_message = ChatMessage(
                conversation_id=conversation_id,
                role=message.role,
                content=message.content,
            )
            self.db.add(new_message)

        self.db.flush()

    # ---------- Long-Term Memory ----------

    def get_long_term_memory(self, user_id: str) -> dict:
        memories = (
            self.db.query(LongTermMemory)
            .filter(LongTermMemory.user_id == user_id)
            .all()
        )

        return {memory.key: memory.value for memory in memories}

    def upsert_long_term_memory(

            self,

            user_id: str,

            key: str,

            value: str,

            source: str = "llm_extraction",

    ) -> dict:

        self.get_or_create_user(user_id)

        memory = (

            self.db.query(LongTermMemory)

            .filter(

                LongTermMemory.user_id == user_id,

                LongTermMemory.key == key,

            )

            .first()

        )

        if memory:

            old_value = memory.value

            old_confidence = memory.confidence

            # Case 1: Same value → reinforce

            if memory.value == value:

                if memory.confidence == "low":

                    memory.confidence = "medium"

                elif memory.confidence == "medium":

                    memory.confidence = "high"

                memory.updated_at = datetime.utcnow()

                self.db.flush()

                return {

                    "status": "reinforced",

                    "key": key,

                    "value": value,

                    "old_confidence": old_confidence,

                    "new_confidence": memory.confidence,

                }

            # Case 2: Conflict → degrade carefully

            if memory.confidence == "high":

                memory.confidence = "medium"

            elif memory.confidence == "medium":

                memory.confidence = "low"

            else:

                memory.confidence = "low"

            memory.updated_at = datetime.utcnow()

            self.db.flush()

            return {

                "status": "conflict",

                "key": key,

                "old_value": old_value,

                "new_value": value,

                "old_confidence": old_confidence,

                "new_confidence": memory.confidence,

            }

        # Case 3: New memory

        memory = LongTermMemory(

            user_id=user_id,

            key=key,

            value=value,

            confidence="medium",

            source=source,

        )

        self.db.add(memory)

        self.db.flush()

        return {

            "status": "created",

            "key": key,

            "value": value,

            "new_confidence": "medium",

        }

    def list_conversations_by_user(self, user_id: str):

        latest_message_subquery = (

            self.db.query(

                ChatMessage.conversation_id.label("conversation_id"),

                func.max(ChatMessage.created_at).label("last_activity_at"),

            )

            .group_by(ChatMessage.conversation_id)

            .subquery()

        )

        results = (

            self.db.query(

                Conversation,

                latest_message_subquery.c.last_activity_at,

            )

            .outerjoin(

                latest_message_subquery,

                Conversation.id == latest_message_subquery.c.conversation_id,

            )

            .filter(Conversation.user_id == user_id)

            .order_by(desc(latest_message_subquery.c.last_activity_at))

            .all()

        )

        conversations = []

        for conversation, last_activity_at in results:
            last_message = (

                self.db.query(ChatMessage)

                .filter(ChatMessage.conversation_id == conversation.id)

                .order_by(ChatMessage.created_at.desc())

                .first()

            )

            conversations.append(

                {

                    "conversation_id": conversation.id,

                    "summary": conversation.summary,

                    "created_at": conversation.created_at,

                    "last_activity_at": last_activity_at or conversation.created_at,

                    "last_message": last_message.content if last_message else None,

                }

            )

        return conversations

    def force_update_long_term_memory(
            self,
            user_id: str,
            key: str,
            value: str,
            source: str = "user_confirmed",
    ) -> dict:
        self.get_or_create_user(user_id)

        memory = (
            self.db.query(LongTermMemory)
            .filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.key == key,
            )
            .first()
        )

        if memory:
            old_value = memory.value
            memory.value = value
            memory.confidence = "high"
            memory.source = source
            memory.updated_at = datetime.utcnow()
            self.db.flush()

            return {
                "status": "updated",
                "key": key,
                "old_value": old_value,
                "new_value": value,
                "confidence": "high",
            }

        memory = LongTermMemory(
            user_id=user_id,
            key=key,
            value=value,
            confidence="high",
            source=source,
        )

        self.db.add(memory)
        self.db.flush()

        return {
            "status": "created",
            "key": key,
            "value": value,
            "confidence": "high",
        }


    def create_pending_memory_conflicts(
            self,
            user_id: str,
            conversation_id: str,
            conflicts: list[dict],
    ):
        for conflict in conflicts:
            pending = PendingMemoryConflict(
                user_id=user_id,
                conversation_id=conversation_id,
                key=conflict["key"],
                old_value=conflict["old_value"],
                new_value=conflict["new_value"],
                status="pending",
            )
            self.db.add(pending)

        self.db.flush()

    def get_pending_memory_conflicts(
            self,
            conversation_id: str,
    ) -> list[PendingMemoryConflict]:
        return (
            self.db.query(PendingMemoryConflict)
            .filter(
                PendingMemoryConflict.conversation_id == conversation_id,
                PendingMemoryConflict.status == "pending",
            )
            .all()
        )

    def resolve_pending_memory_conflicts(
            self,
            conversation_id: str,
            status: str,
    ):
        conflicts = self.get_pending_memory_conflicts(conversation_id)

        for conflict in conflicts:
            conflict.status = status
            conflict.resolved_at = datetime.utcnow()

        self.db.flush()