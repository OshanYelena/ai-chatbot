from fastapi import FastAPI
from app.core.config import settings


app = FastAPI(
    title= settings.APP_Name,
    version=settings.APP_VERSION,
    description="A production-style hello world chatbot backend"
)


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_Name} API is running",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"

    }
