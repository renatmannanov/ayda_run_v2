import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    """
    Application settings with validation.
    
    Uses Pydantic for type safety and automatic validation.
    Values are loaded from environment variables.
    
    TODO: Add your project-specific settings here.
    """
    
    # === Core Settings ===
    bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN", description="Telegram Bot Token")
    app_url: Optional[str] = Field(None, alias="WEB_APP_URL", description="Public URL of the app")
    
    # === Database ===
    database_url: str = Field(
        default="sqlite:///./app.db",
        description="Database connection URL"
    )
    
    # === Optional Integrations ===
    google_sheets_credentials: Optional[str] = Field(
        None,
        alias="GOOGLE_SHEETS_CREDENTIALS",
        description="Google Sheets credentials (file path or JSON)"
    )
    
    mongodb_uri: Optional[str] = Field(
        None,
        alias="MONGODB_URI",
        description="MongoDB connection URI"
    )
    
    # === Features ===
    max_free_users: int = Field(
        default=1000,
        description="Maximum free tier users"
    )
    
    enable_analytics: bool = Field(
        default=False,
        description="Enable analytics tracking"
    )
    
    # === Development ===
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # === Rate Limiting ===
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_global: str = Field(default="200/minute", description="Global rate limit")
    rate_limit_create: str = Field(default="10/minute", description="Create endpoints limit")
    rate_limit_read: str = Field(default="100/minute", description="Read endpoints limit")
    
    @field_validator('database_url')
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        """Fix Render/Railway postgres:// URL to postgresql://"""
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v
    
    @field_validator('google_sheets_credentials')
    @classmethod
    def validate_credentials(cls, v: Optional[str]) -> Optional[str]:
        """Validate Google Sheets credentials"""
        if v:
            # Check if it's a file path
            if not v.strip().startswith('{') and not os.path.exists(v):
                print(f"Warning: Credentials file not found at: {v}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Initialize settings
settings = Settings()

# Backward compatibility: expose as config dict for existing code
config = {
    "bot_token": settings.bot_token,
    "credentials_path": settings.google_sheets_credentials,
    "mongodb_uri": settings.mongodb_uri,
}
