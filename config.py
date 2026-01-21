import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict

class Settings(BaseSettings):
    """
    Application settings with validation.
    
    Uses Pydantic for type safety and automatic validation.
    Values are loaded from environment variables.
    
    TODO: Add your project-specific settings here.
    """
    
    # === Core Settings ===
    bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN", description="Telegram Bot Token")
    bot_username: str = Field(..., alias="BOT_USERNAME", description="Bot username without @")
    app_url: Optional[str] = Field(None, alias="WEB_APP_URL", description="Public URL of the app")
    base_url: Optional[str] = Field(None, alias="BASE_URL", description="Base URL for webhooks (e.g., ngrok URL)")
    admin_chat_id: Optional[int] = Field(None, alias="ADMIN_CHAT_ID", description="Admin Telegram Chat ID for notifications")
    
    # === Database ===
    database_url: str = Field(
        default="sqlite:///./app.db",
        description="Database connection URL"
    )
    prod_database_url: Optional[str] = Field(
        None,
        description="Production database URL (Railway/Render)"
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

    # === GPX Storage ===
    gpx_channel_id: int = Field(
        ...,
        alias="GPX_CHANNEL_ID",
        description="Telegram channel ID for storing GPX files"
    )

    # === Feedback ===
    feedback_chat_id: Optional[int] = Field(
        None,
        alias="FEEDBACK_CHAT_ID",
        description="Telegram group ID for forwarding user feedback"
    )

    # === Rate Limiting ===
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_global: str = Field(default="200/minute", description="Global rate limit")
    rate_limit_create: str = Field(default="10/minute", description="Create endpoints limit")
    rate_limit_read: str = Field(default="100/minute", description="Read endpoints limit")

    # === Logging ===
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    # === CORS ===
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )

    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v: list[str], info) -> list[str]:
        """Validate CORS origins - no wildcards in production"""
        # Get debug value from config - accessing model context if possible or assuming default.
        # info.data contains other fields already validated?
        # Pydantic v2: info.data is available
        debug = info.data.get('debug', False)

        if "*" in v and not debug:
            raise ValueError(
                "Wildcard CORS origins (*) are not allowed in production. "
                "Please specify exact origins."
            )
        return v
    
    @field_validator('app_url')
    @classmethod
    def ensure_https_and_trailing_slash(cls, v: Optional[str]) -> Optional[str]:
        """Ensure app_url has https:// prefix and trailing slash"""
        if v is None:
            return None
        v = v.strip()
        if v.startswith('http://'):
            v = v.replace('http://', 'https://', 1)
        elif not v.startswith('https://'):
            v = f'https://{v}'
        # Ensure trailing slash for proper URL concatenation
        if not v.endswith('/'):
            v = f'{v}/'
        return v

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

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# Initialize settings
settings = Settings()

# Backward compatibility: expose as config dict for existing code
config = {
    "bot_token": settings.bot_token,
    "credentials_path": settings.google_sheets_credentials,
    "mongodb_uri": settings.mongodb_uri,
}
