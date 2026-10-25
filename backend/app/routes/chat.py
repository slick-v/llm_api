import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.rate_limit import RateLimiter
from app.schemas import ChatRequest, ChatResponse
from app.services.llm import get_reply, stream_reply
from app.models import User
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

user_limiter = RateLimiter(settings.user_limit_per_minute, 60)
global_minute_limiter = RateLimiter(settings.global_limit_per_minute, 60)
global_day_limiter = RateLimiter(settings.global_limit_per_day, 24 * 60 * 60)

# what users see; the real error only goes to the server logs
LLM_ERROR = "The AI service isn't available right now. Please try again in a moment."


def check_limits(user_id: str):
    if not user_limiter.allow(user_id):
        raise HTTPException(
            status_code=429,
            detail="You're sending messages too fast. Wait a minute and try again.",
        )
    if not global_minute_limiter.allow("all") or not global_day_limiter.allow("all"):
        logger.warning("Global rate limit reached")
        raise HTTPException(
            status_code=429,
            detail="The app is busy right now. Please try again later.",
        )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, user: User = Depends(get_current_user)):
    check_limits(str(user.id))
    messages = [m.model_dump() for m in request.messages]
    try:
        reply, tokens_used = get_reply(messages, request.mode, user_id=user.id, session_id=request.conversation_id)
    except Exception:
        logger.exception("LLM call failed for user %s", user.id)
        raise HTTPException(status_code=502, detail=LLM_ERROR)
    return ChatResponse(
        reply=reply,
        tokens_used=tokens_used,
        conversation_id=request.conversation_id,
    )


@router.post("/chat/stream")
def chat_stream(request: ChatRequest,  user: User = Depends(get_current_user)):
    check_limits(str(user.id))
    user_id = user.id  # plain value for the generator below, which runs after the request
    messages = [m.model_dump() for m in request.messages]

    # pull the first chunk now so errors like bad credentials or model name
    # come back as a 502 instead of a 200 with the error in the body
    chunks = stream_reply(messages, request.mode, user_id=user_id, session_id=request.conversation_id)
    try:
        first = next(chunks, "")
    except Exception:
        logger.exception("LLM stream failed for user %s", user_id)
        raise HTTPException(status_code=502, detail=LLM_ERROR)

    def generate():
        yield first
        try:
            yield from chunks
        except Exception:
            logger.exception("LLM stream broke mid-reply for user %s", user_id)
            yield "\n\n[The reply was cut off. Please try again.]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")