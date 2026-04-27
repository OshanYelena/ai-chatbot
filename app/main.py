from fastapi import FastAPI

app = FastAPI(
    title="Simple AI Chatbot",
    description="A production-style hello world chatbot backend"
)


@app.get("/")
async def root():
    return {
        "message": "Simple AI Chatbot API is running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"

    }
