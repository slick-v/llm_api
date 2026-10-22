from pathlib import Path


from pydantic_settings import BaseSettings, SettingsConfigDict


# find .env in the project root, 
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    groq_api_key: str
    model_name: str = "openai/gpt-oss-20b"
    max_tokens: int = 1000


    model_config = SettingsConfigDict(env_file=ENV_FILE)



settings = Settings()