import time

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from opentelemetry import trace

from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)
tracer = trace.get_tracer(__name__)

VERIFY_ENDPOINT = f"{settings.AUTH_GATEWAY_URL}/api/v1/auth/verify"

bearer_scheme = HTTPBearer(auto_error=False)


def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    start_time = time.perf_counter()

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with tracer.start_as_current_span("auth.verify_token") as span:
        span.set_attribute("auth.operation", "verify_token")
        span.set_attribute("auth.gateway_url", VERIFY_ENDPOINT)

        try:
            logger.info(
                "auth_verify_started",
                extra={
                    "trace_id": trace_id,
                    "event": "auth_verify_started",
                    "operation": "verify_token",
                },
            )

            response = httpx.get(
                VERIFY_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {credentials.credentials}",
                    "X-Trace-ID": trace_id or "",
                },
                timeout=5.0,
            )

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            span.set_attribute("auth.status_code", response.status_code)
            span.set_attribute("auth.latency_ms", latency_ms)

        except httpx.RequestError as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            span.record_exception(exc)
            span.set_attribute("auth.status", "gateway_unreachable")
            span.set_attribute("auth.latency_ms", latency_ms)

            logger.exception(
                "auth_gateway_unreachable",
                extra={
                    "trace_id": trace_id,
                    "event": "auth_gateway_unreachable",
                    "operation": "verify_token",
                    "error_message": str(exc),
                },
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth gateway unreachable",
            ) from exc

        if response.status_code != 200:
            span.set_attribute("auth.status", "invalid_token")

            logger.info(
                "auth_verify_failed",
                extra={
                    "trace_id": trace_id,
                    "event": "auth_verify_failed",
                    "operation": "verify_token",
                },
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        data = response.json()

        if not data.get("valid"):
            span.set_attribute("auth.status", "token_validation_failed")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = data["user_id"]

        span.set_attribute("auth.status", "success")
        span.set_attribute("auth.user_id", user_id)

        logger.info(
            "auth_verify_success",
            extra={
                "trace_id": trace_id,
                "event": "auth_verify_success",
                "operation": "verify_token",
                "user_id": user_id,
            },
        )

        return user_id