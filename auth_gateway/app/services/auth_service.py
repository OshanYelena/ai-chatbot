import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import setup_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.db.models import AuthUser, RefreshToken

logger = setup_logger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain.encode(), salt).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _hash_token(raw_token: str) -> str:
    """SHA-256 of the raw refresh token for DB storage (never store JWTs plainly)."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Service ───────────────────────────────────────────────────────────────────

class AuthService:

    # ── Register ──────────────────────────────────────────────────────────────

    def register(self, db: Session, email: str, password: str) -> AuthUser:
        existing = db.query(AuthUser).filter(AuthUser.email == email).first()
        if existing:
            raise ValueError("Email already registered")

        user = AuthUser(
            email=email,
            hashed_password=_hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("User registered: %s (id=%s)", email, user.id)
        return user

    # ── Login ─────────────────────────────────────────────────────────────────

    def login(self, db: Session, email: str, password: str) -> dict:
        user: AuthUser | None = db.query(AuthUser).filter(AuthUser.email == email).first()

        if not user or not _verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is disabled")

        access_token = create_access_token(user_id=user.id, email=user.email)
        refresh_token_raw = create_refresh_token(user_id=user.id)

        # Persist hashed refresh token
        expires_at = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh_token_raw),
            expires_at=expires_at,
        )
        db.add(rt)
        db.commit()

        logger.info("User logged in: %s", email)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_raw,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self, db: Session, refresh_token_raw: str) -> dict:
        payload = verify_refresh_token(refresh_token_raw)
        if not payload:
            raise ValueError("Invalid or expired refresh token")

        token_hash = _hash_token(refresh_token_raw)
        rt: RefreshToken | None = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked == False)
            .first()
        )

        if not rt:
            raise ValueError("Refresh token not found or already revoked")

        if rt.expires_at.replace(tzinfo=timezone.utc) < _now():
            raise ValueError("Refresh token expired")

        user: AuthUser | None = db.query(AuthUser).filter(AuthUser.id == rt.user_id).first()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Rotate: revoke old token, issue new pair
        rt.revoked = True
        db.commit()

        new_access = create_access_token(user_id=user.id, email=user.email)
        new_refresh_raw = create_refresh_token(user_id=user.id)
        new_expires_at = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(new_refresh_raw),
            expires_at=new_expires_at,
        )
        db.add(new_rt)
        db.commit()

        logger.info("Tokens rotated for user_id=%s", user.id)
        return {
            "access_token": new_access,
            "refresh_token": new_refresh_raw,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    # ── Logout ────────────────────────────────────────────────────────────────

    def logout(self, db: Session, refresh_token_raw: str) -> None:
        token_hash = _hash_token(refresh_token_raw)
        rt: RefreshToken | None = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )
        if rt:
            rt.revoked = True
            db.commit()
            logger.info("Refresh token revoked for user_id=%s", rt.user_id)

    # ── Verify (used by chatbot service) ──────────────────────────────────────

    def verify(self, db: Session, access_token: str) -> dict:
        """
        Returns {"valid": True, "user_id": ..., "email": ...}
        or      {"valid": False, "user_id": None, "email": None}
        """
        from app.core.security import verify_access_token

        payload = verify_access_token(access_token)
        if not payload:
            return {"valid": False, "user_id": None, "email": None}

        user: AuthUser | None = db.query(AuthUser).filter(AuthUser.id == payload["sub"]).first()
        if not user or not user.is_active:
            return {"valid": False, "user_id": None, "email": None}

        return {"valid": True, "user_id": user.id, "email": user.email}


auth_service = AuthService()
