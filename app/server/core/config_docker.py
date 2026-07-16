from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.server.core.logger import logger


class Settings(BaseSettings):
    app_env: str = "dev"
    llm_provider: str = "gemini"
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"

    supabase_url: str
    supabase_key: str
    database_url: str

    livekit_url: str | None = None
    livekit_api_key: str | None = None
    livekit_api_secret: str | None = None

    livekit_room_prefix: str = "voicehire-"
    livekit_stt_model: str = "deepgram/nova-3"
    livekit_stt_language: str = "en"

    voicehire_api_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        extra="ignore",
    )


settings = Settings()

logger.success("Settings loaded")
logger.info(f"APP_ENV = {settings.app_env}")
logger.info(f"GEMINI_MODEL = {settings.gemini_model}")
logger.info(f"SUPABASE_URL = {settings.supabase_url}")