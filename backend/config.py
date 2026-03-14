from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/linkedin_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LinkedIn credentials
    linkedin_email: str = ""
    linkedin_password: str = ""
    linkedin_session_cookie: str = ""

    # AI / LLM
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "linkedin_profiles"

    # Automation limits
    daily_limit_per_region: int = 20
    session_limit: int = 10
    min_delay_seconds: int = 8
    max_delay_seconds: int = 20
    dry_run: bool = False

    # Notifications
    slack_webhook_url: str = ""
    alert_email: str = ""

    # App
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
