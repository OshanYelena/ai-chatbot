import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey

from sqlalchemy.orm import relationship

from app.db.database import Base


class Conversation(Base):
    __tablename__ = "Conversations"
    id = Column(String, primary_key=True, default=lambda : str (uuid.uuid4()))
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow())

    message = relationship(
        "chatMessages",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    memories = relationship(
        "LongTermMemory",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

class ChatMessage(Base):

    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")

class LongTermMemory(Base):

    __tablename__ = "long_term_memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="memories")