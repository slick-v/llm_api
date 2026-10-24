from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# find .env in the project root, 
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    llm_provider: Literal["groq", "bedrock"] = "groq"
    max_tokens: int = 1000

    # GROQ
    groq_api_key: str
    model_name: str = "openai/gpt-oss-20b"
    # max_tokens: int = 1000
    # BEDROCK
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "apac.amazon.nova-micro-v1:0"

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")



settings = Settings()