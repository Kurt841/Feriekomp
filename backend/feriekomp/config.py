import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "feriekompensasjon.db"


class Settings(BaseSettings):
    """Konfigurasjon lastet fra miljøvariabler med standardverdier."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("ENV", "FLASK_ENV"),
        description="Miljø: 'development' eller 'production'. Styrer app-oppførsel (database, auto_create_db, etc.), ikke servervalg (Gunicorn/uvicorn styres av oppstartskommando).",
    )
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    dev_database_url: str | None = Field(default=None, alias="DEV_DATABASE_URL")

    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"],
        alias="ALLOWED_ORIGINS",
        description="CORS origins: For produksjon, sett til din offentlige frontend-domene (f.eks. https://feriekomp.example.com)",
    )
    next_dev_origin: str | None = Field(default=None, alias="NEXT_DEV_ORIGIN")
    force_https: bool = Field(default=False, alias="FORCE_HTTPS")
    trust_proxy: bool = Field(
        default=False,
        alias="TRUST_PROXY",
        description="Stol på X-Forwarded-* headers fra reverse proxy. MÅ settes til true i produksjon bak Nginx.",
    )
    auto_create_db: bool | None = Field(
        default=None,
        alias="AUTO_CREATE_DB",
        description="Auto-opprett database-tabeller. Sett til false i produksjon.",
    )
    rate_limit_storage_uri: str = Field(
        default="memory://",
        alias="RATE_LIMIT_STORAGE_URI",
        description="Rate limit storage: 'memory://' (per-prosess) eller 'redis://...' (delt mellom workers)",
    )

    ai_enabled: bool = Field(default=False, alias="ENABLE_AI")
    ai_timeout: int = Field(default=30, alias="AI_TIMEOUT")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")

    ollama_url: str = Field(default="http://localhost:11434", alias="OLLAMA_URL")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")

    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-4o-mini", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")

    @computed_field  # type: ignore[misc]
    @property
    def effective_database_url(self) -> str:
        """Foretrekker dev DB i ikke-prod, ellers faller tilbake til hoved-DB eller lokal SQLite."""
        if self.environment == "production" and self.database_url:
            return self.database_url

        if self.dev_database_url:
            return self.dev_database_url

        if self.database_url:
            return self.database_url

        return f"sqlite:///{DEFAULT_DB_PATH}"

    @computed_field  # type: ignore[misc]
    @property
    def cors_origins(self) -> list[str]:
        """Normalisert liste over tillatte origins."""
        origins = [o.strip().rstrip("/") for o in self.allowed_origins if o.strip()]
        if self.next_dev_origin:
            origins.append(self.next_dev_origin.strip().rstrip("/"))
        seen = {}
        for origin in origins:
            seen[origin] = None
        return list(seen.keys())

    @computed_field  # type: ignore[misc]
    @property
    def allow_auto_create_db(self) -> bool:
        """
        Tillater automatisk tabellopprettelse i ikke-prod med mindre eksplisitt deaktivert.
        
        PRODUKSJON: Sett AUTO_CREATE_DB=false for å forhindre automatisk tabellopprettelse.
        """
        if self.auto_create_db is not None:
            return self.auto_create_db
        return self.environment != "production"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        if isinstance(value, str):
            return [o.strip() for o in value.split(",") if o.strip()]
        return value

    @field_validator("rate_limit_storage_uri", mode="before")
    @classmethod
    def normalize_rate_limit_storage_uri(cls, value):
        if value is None:
            return "memory://"
        if isinstance(value, str) and not value.strip():
            return "memory://"
        return value


def load_settings() -> Settings:
    """Laster .env-filer før instansiering av innstillinger."""
    # Last først fra repo-rot (hvis den eksisterer)
    root_env = PROJECT_ROOT / ".env"
    if root_env.exists():
        load_dotenv(dotenv_path=root_env, override=False)
    # Last deretter fra backend-mappen (overskriver ikke eksisterende)
    load_dotenv()
    raw_origins = os.getenv("ALLOWED_ORIGINS")
    if raw_origins is not None and not raw_origins.strip().startswith("["):
        normalized = [o.strip() for o in raw_origins.split(",") if o.strip()]
        if not normalized:
            normalized = ["http://localhost:3000", "http://localhost:8080"]
        os.environ["ALLOWED_ORIGINS"] = json.dumps(normalized)
    return Settings()


settings = load_settings()
