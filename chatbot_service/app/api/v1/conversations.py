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
