from typing import Literal

from pydantic import BaseModel,Field


MAX_MESSAGE_CHARS = 8000
MAX_MESSAGES = 20

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str =Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class ChatRequest(BaseModel):
    messages: list[Message] =Field(min_length=1, max_length=MAX_MESSAGES)
    conversation_id: str | None = None
    mode: Literal["assistant", "tutor", "coder", "interviewer"] = "assistant"


class ChatResponse(BaseModel):
    reply:str
    tokens_used: int
    conversation_id: str | None = None