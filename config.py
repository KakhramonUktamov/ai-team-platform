from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM Provider ──────────────────────────────────────────
    llm_provider: str = "openai"          # "openai" or "anthropic"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

   # ── API ───────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_secret_key: str = "change-me-in-production"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8501"]

    # ── Database ──────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/ai_team_platform"
    database_url_sync: str = "postgresql://user:password@localhost:5432/ai_team_platform"

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── ChromaDB ──────────────────────────────────────────────
    chroma_persist_dir: str = "./data/chroma"
    pinecone_api_key: str = ""
    pinecone_index_name: str = ""

    # ── Environment ───────────────────────────────────────────
    environment: str = "development"
    debug: bool = True

    # --- Auth ---
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwks_url: str = ""

    # ── Convenience properties ────────────────────────────────
    @property
    def is_openai(self) -> bool:
        return self.llm_provider.lower() == "openai"

    @property
    def is_anthropic(self) -> bool:
        return self.llm_provider.lower() == "anthropic"

    @property
    def active_model(self) -> str:
        return self.openai_model if self.is_openai else self.anthropic_model

    @property
    def active_api_key(self) -> str:
        return self.openai_api_key if self.is_openai else self.anthropic_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Convenient module-level instance
settings = get_settings()