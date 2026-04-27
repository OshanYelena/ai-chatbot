from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.v1.chat import router as chat_router
from app.db.database import get_db
from app.db.health import check_db_connection

app = FastAPI(
    title= settings.APP_Name,
    version=settings.APP_VERSION,
    description="A production-style hello world chatbot backend"
)

app.include_router(chat_router, prefix="/api/v1")


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
