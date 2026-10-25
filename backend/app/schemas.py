from typing import Literal

from pydantic import BaseModel,Field,ConfigDict,EmailStr


MAX_MESSAGE_CHARS = 8000
MAX_MESSAGES = 20

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str =Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class ChatRequest(BaseModel):
    messages: list[Message] =Field(min_length=1, max_length=MAX_MESSAGES)
    conversation_id: str | None = Field(default=None, max_length=64)
    mode: Literal["assistant", "tutor", "coder", "interviewer"] = "assistant"


class ChatResponse(BaseModel):
    reply:str
    tokens_used: int
    conversation_id: str | None = None


# USER
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserOut(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)

# TOKEN
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut