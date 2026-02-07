from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Rural Health Triage API"
    environment: str = "development"
    log_level: str = "INFO"
    timezone: str = "Asia/Kolkata"

    database_url: str
    groq_api_key: str
    groq_vision_model: str = "llama-3.2-11b-vision-preview"
    secret_key: str
    image_upload_dir: str = "uploads"
    frontend_url: str = "http://localhost:5173"
    production_url: str | None = None
    public_app_url: str | None = None
    skip_db_check: bool = False

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str | None = None
    twilio_sms_from: str | None = None
    asha_worker_number: str | None = None

    cors_allow_origins: List[str] = []

    def computed_origins(self) -> List[str]:
        origins = [self.frontend_url]
        if self.production_url:
            origins.append(self.production_url)
        if self.cors_allow_origins:
            origins.extend(self.cors_allow_origins)
        return list(dict.fromkeys(origins))


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    configure_logging(settings.log_level)
    return settings
