from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.v1.chat import router as chat_router
from app.db.database import get_db
from app.db.health import check_db_connection
from app.middleware.trace_middleware import TraceMiddleware
from app.core.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from app.core.telemetry import setup_telemetry

from app.api.v1.conversations import router as conversations_router

app = FastAPI(
    title= settings.APP_Name,
    version=settings.APP_VERSION,
    description="A production-style hello world chatbot backend"
)

setup_telemetry(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(TraceMiddleware)
app.include_router(chat_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_Name} API is running",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")

def health_check(db: Session = Depends(get_db)):
    check_db_connection(db)
    return {
        "status": "healthy",
        "database": "connected",
    }


@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    check_db_connection(db)
    return {
        "status": "ready",
        "database": "connected"

    }