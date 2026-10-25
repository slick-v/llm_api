from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# find .env in the project root, 
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    llm_provider: Literal["groq", "bedrock"] = "groq"
    max_tokens: int = 1000

    # GROQ
    groq_api_key: str | None =None
    model_name: str = "openai/gpt-oss-20b"

    # BEDROCK
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "apac.amazon.nova-micro-v1:0"

    # LIMITS
    user_limit_per_minute: int = 10
    global_limit_per_minute: int = 30
    global_limit_per_day: int = 1000

    # DATABASE
    database_url: str = "postgresql+psycopg://llm:llm@localhost:5432/llm_chat"

    # AUTH
    jwt_secret: str #required app wont start without it 
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60*24 #1day

    # OBSERVABILITY
    app_env: str = "local"   # set APP_ENV=production on the server
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_base_url: str = "https://cloud.langfuse.com"
    langfuse_log_content: bool = True  # False = send only numbers, not the chat text
    sentry_dsn: str | None = None

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")



settings = Settings()