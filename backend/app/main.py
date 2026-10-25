import logging


from fastapi import FastAPI

from app.routes.chat import router as chat_router


# without this, our logger.exception() lines may not show up in docker logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="LLM Chat API")

app.include_router(chat_router)



@app.get("/health")
def health():
    return {"status": "ok"}