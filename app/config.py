from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///" + str(Path(__file__).resolve().parent.parent / "academic_tracker.db")

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3"

    # OpenAI
    openai_api_key: str | None = None
    openai_default_model: str = "gpt-4o"

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8")


settings = Settings()
