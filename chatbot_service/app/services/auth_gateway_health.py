import httpx

from app.core.config import settings


def check_auth_gateway_connection() -> bool:
    url = f"{settings.AUTH_GATEWAY_URL}/ready"

    response = httpx.get(url, timeout=5.0)
    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ready":
        raise RuntimeError("Auth gateway is not ready")

    return True