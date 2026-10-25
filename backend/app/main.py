import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app import models
from app.db import Base, engine
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router


# without this, our logger.exception() lines may not show up in docker logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app:FastAPI):
    # creates tables that don't exist yet (never changes existing ones);
    # move to Alembic migrations once the schema starts changing
    Base.metadata.create_all(engine)
    yield

app = FastAPI(title="LLM Chat API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(chat_router)



@app.get("/health")
def health():
    return {"status": "ok"}