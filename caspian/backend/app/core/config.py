from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Caspian AI Assistant"

    # Database
    database_url: str = (
        "postgresql+asyncpg://caspian_user:password@localhost:5433/caspian_db"
    )
    sqlalchemy_echo: bool = False

    # LLM Provider selection: 'gemini' | 'openai' | 'anthropic'
    llm_provider: str = "gemini"

    # Integrations
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    discord_token: str | None = None

    # Default personal user
    default_username: str = "sir"
    default_user_password: str = "Vinitus@123"
    create_default_user_on_startup: bool = True

    # Security / Auth
    secret_key: str = "Vinitus@123"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


settings = Settings()