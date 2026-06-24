# app/server/core/config.py

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.server.core.logger import logger

BASE_DIR = Path(__file__).resolve().parents[1]


def resolve_env_file() -> Path | None:
    app_env = os.getenv("APP_ENV", "dev").strip().lower()

    candidates: list[Path] = []

    if app_env in {"dev", "development"}:
        candidates = [
            BASE_DIR / ".env.dev",
            BASE_DIR / ".env",
            BASE_DIR / ".env.prod",
        ]
    elif app_env in {"prod", "production"}:
        candidates = [
            BASE_DIR / ".env.prod",
            BASE_DIR / ".env",
            BASE_DIR / ".env.dev",
        ]
    else:
        candidates = [
            BASE_DIR / ".env",
            BASE_DIR / ".env.dev",
            BASE_DIR / ".env.prod",
        ]

    for path in candidates:
        if path.exists():
            logger.success(f"using env file: {path}")
            return path

    logger.warning("no env file found; falling back to process environment")
    return None


ENV_FILE = resolve_env_file()
logger.info(f"ENV_FILE = {ENV_FILE}")


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
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

logger.success("Settings loaded")
logger.info(f"APP_ENV = {settings.app_env}")
logger.info(f"GEMINI_MODEL = {settings.gemini_model}")
logger.info(f"SUPABASE_URL = {settings.supabase_url}")