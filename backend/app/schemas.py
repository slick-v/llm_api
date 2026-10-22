from typing import Literal

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    conversation_id: str | None = None
    mode: Literal["assistant", "tutor", "coder", "interviewer"] = "assistant"


class ChatResponse(BaseModel):
    reply:str
    tokens_used: int
    conversation_id: str | None = None