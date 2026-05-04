"""
app/services/jwt_verifier.py

FastAPI dependency that validates a Bearer token by calling the auth gateway's
GET /api/v1/auth/verify endpoint.

Returns the verified user_id on success, raises HTTP 401 on failure.

Usage in any endpoint:

    from app.services.jwt_verifier import verify_token

    @router.post("/chat/")
    def chat(
        request: Request,
        payload: ChatRequest,
        user_id: str = Depends(verify_token),   # ← identity comes from JWT
        db: Session = Depends(get_db),
    ):
        ...
"""

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

VERIFY_ENDPOINT = f"{settings.AUTH_GATEWAY_URL}/api/v1/auth/verify"

bearer_scheme = HTTPBearer(auto_error=False)


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """
    Calls the auth gateway to validate the Bearer token.
    Returns the verified user_id string on success.
    Raises HTTP 401/503 on failure.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        response = httpx.get(
            VERIFY_ENDPOINT,
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            timeout=5.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth gateway unreachable",
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    data = response.json()
    if not data.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return data["user_id"]
