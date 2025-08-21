from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
import os
import sys

# Determine the environment file location silently
def find_env_file():
    """Find the .env file in various possible locations."""
    # Define potential locations for the .env file
    current_dir = os.getcwd()
    backend_dir = os.path.join(current_dir, 'backend')
    parent_backend_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    
    possible_env_files = [
        os.path.join(current_dir, '.env'),
        os.path.join(backend_dir, '.env'),
        os.path.join(parent_backend_dir, '.env'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env')),
    ]
    
    # Find the first existing .env file
    for env_path in possible_env_files:
        if os.path.exists(env_path):
            return env_path
    
    return None

# Find the .env file silently
env_file = find_env_file()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_file if env_file else None,
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