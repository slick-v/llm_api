from fastapi import FastAPI

from app.routes.chat import router as chat_router

app = FastAPI(title="LLM Chat API")

app.include_router(chat_router)



@app.get("/health")
def health():
    return {"status": "ok"}