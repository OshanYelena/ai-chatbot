from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.logger import setup_logger
from app.db.database import get_db
from app.db.models import AuthUser
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    VerifyResponse,
)
from app.services.auth_service import auth_service
from app.services.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = setup_logger(__name__)


# ── Register ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.register(db=db, email=payload.email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return RegisterResponse(user_id=user.id, email=user.email)


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive access + refresh tokens",
)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    try:
        tokens = auth_service.login(db=db, email=payload.email, password=payload.password)
    except ValueError as exc:
        # Use 401 for auth failures, never 404 — prevents user enumeration
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    logger.info(
        "login_success",
        extra={"trace_id": request.state.trace_id, "email": payload.email},
    )
    return TokenResponse(**tokens)


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new token pair (rotation)",
)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        tokens = auth_service.refresh(db=db, refresh_token_raw=payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return TokenResponse(**tokens)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token (server-side logout)",
)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    auth_service.logout(db=db, refresh_token_raw=payload.refresh_token)


# ── Verify (internal — called by chatbot service) ─────────────────────────────

@router.get(
    "/verify",
    response_model=VerifyResponse,
    summary="Validate a Bearer access token — used internally by the chatbot service",
)
def verify(
    current_user: AuthUser = Depends(get_current_user),
):
    """
    The chatbot service calls this endpoint to validate a token before
    processing any chat request. Returns the user_id so the chatbot
    service knows which user is making the request.
    """
    return VerifyResponse(
        valid=True,
        user_id=current_user.id,
        email=current_user.email,
    )


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    summary="Return the currently authenticated user's profile",
)
def me(current_user: AuthUser = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
    }
