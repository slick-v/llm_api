import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app import models
from app.db import Base, engine, get_db
from app.observability import init_sentry, langfuse
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router


# without this, our logger.exception() lines may not show up in docker logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

# before the app is created, so Sentry can hook into FastAPI
init_sentry()

@asynccontextmanager
async def lifespan(app:FastAPI):
    # creates tables that don't exist yet (never changes existing ones);
    # move to Alembic migrations once the schema starts changing
    Base.metadata.create_all(engine)
    yield
    # send LLM traces still waiting in memory before the process exits
    langfuse.shutdown()

app = FastAPI(title="LLM Chat API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(chat_router)



@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Used by Docker and UptimeRobot: 200 only when the database answers too."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: database unreachable")
        return JSONResponse(status_code=503, content= {"status": "error", "database":"down"})
    
    return {"status": "ok", "database":"ok"}