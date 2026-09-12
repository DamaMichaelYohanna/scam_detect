from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None

    # Exa AI
    EXA_API_KEY: str = ""

    # AI Provider Selection ("openai" or "gemini")
    AI_PROVIDER: str = "openai"

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Google Gemini Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Server / Webhook / Polling
    WEBHOOK_URL: Optional[str] = None
    POLLING_MODE: bool = True  # Defaults to True for local development (reliable instant message receipt)
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Moderation & Scam Detection Actions
    RISK_THRESHOLD: float = 0.7            # Threshold for warning message in group
    BAN_THRESHOLD: float = 0.85            # Threshold (0.0 to 1.0) to auto-ban/kick scammer
    AUTO_WARN: bool = True                 # Post warning reply in group
    AUTO_BAN: bool = True                  # Auto-remove/ban user if confidence >= BAN_THRESHOLD
    AUTO_DELETE_SCAM_MESSAGE: bool = True  # Automatically delete the malicious message

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
