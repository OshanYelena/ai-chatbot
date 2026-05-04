from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth import router as auth_router
from app.core.config import settings
from app.db.database import get_db
from app.db.health import check_db_connection
from app.middleware.trace_middleware import TraceMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="JWT Auth Gateway — issues and verifies tokens for the AI Chatbot Backend",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(TraceMiddleware)
app.include_router(auth_router, prefix="/api/v1")


@app.get("/", tags=["System"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["System"])
def health(db: Session = Depends(get_db)):
    check_db_connection(db)
    return {"status": "healthy", "database": "connected"}


@app.get("/ready", tags=["System"])
def ready(db: Session = Depends(get_db)):
    check_db_connection(db)
    return {"status": "ready", "database": "connected"}
