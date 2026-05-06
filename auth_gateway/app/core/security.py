from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)

# Token type constants
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, email: str) -> str:
    expire = _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "type": ACCESS_TOKEN_TYPE,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "iat": _now(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "type": REFRESH_TOKEN_TYPE,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "iat": _now(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT. Returns the payload dict or None if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT decode failed: %s", exc)
        return None


def verify_access_token(token: str) -> Optional[dict]:
    """
    Decode and assert token type is 'access'. Returns payload or None.
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        logger.warning("Token type mismatch: expected access, got %s", payload.get("type"))
        return None
    return payload


def verify_refresh_token(token: str) -> Optional[dict]:
    """
    Decode and assert token type is 'refresh'. Returns payload or None.
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        logger.warning("Token type mismatch: expected refresh, got %s", payload.get("type"))
        return None
    return payload
