from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas import ChatRequest, ChatResponse
from app.services.llm import get_reply, stream_reply

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = [m.model_dump() for m in request.messages]
    try:
        reply, tokens_used = get_reply(messages, request.mode)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")
    return ChatResponse(
        reply=reply,
        tokens_used=tokens_used,
        conversation_id=request.conversation_id,
    )


@router.post("/chat/stream")  # NEW
def chat_stream(request: ChatRequest):
    messages = [m.model_dump() for m in request.messages]

    # pull the first chunk now so errors like a bad API key or model name
    # come back as a 502 instead of a 200 with the error in the body
    chunks = stream_reply(messages, request.mode)
    try:
        first = next(chunks, "")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    def generate():
        yield first
        try:
            yield from chunks
        except Exception as e:
            yield f"\n\n[Error: {e}]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")

