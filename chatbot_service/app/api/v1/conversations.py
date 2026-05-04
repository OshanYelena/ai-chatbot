from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.rate_limiter import limiter
from app.db.database import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ConversationListItem
from app.services.jwt_verifier import verify_token  # ← auth dependency

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("/", response_model=List[ConversationListItem])
@limiter.limit("30/minute")
def list_conversations(
    request: Request,
    user_id: str = Depends(verify_token),   # ← from JWT, not query param
    db: Session = Depends(get_db),
):
    repo = ConversationRepository(db)
    return repo.list_conversations_by_user(user_id)


@router.get("/{conversation_id}/messages", response_model=ConversationMessagesResponse)
@limiter.limit("30/minute")
def get_conversation_messages(
    conversation_id: str,
    request: Request,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    Return all messages for a conversation, scoped to the authenticated user.
    Used by the frontend to restore message history when switching conversations.
    """
    repo = ConversationRepository(db)

    # Verify this conversation belongs to the requesting user
    conversation = repo.get_conversation(user_id=user_id, conversation_id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = repo.get_messages(conversation_id)

    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        summary=conversation.summary or None,
        messages=[
            MessageItem(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )

