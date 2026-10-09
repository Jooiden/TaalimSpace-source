from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    vapid_private_key: SecretStr = SecretStr("")
    vapid_public_key: str = ""
    vapid_contact: str = ""
    frontend_url: str = "http://127.0.0.1:5173"
    cookie_secure: bool = False
    serve_frontend: bool = False
    stripe_secret_key: SecretStr = SecretStr("")
    stripe_webhook_secret: SecretStr = SecretStr("")
    brevo_api_key: SecretStr = SecretStr("")
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_from: str = ""
    app_name: str = "TaalimSpace"
    demo_mode: bool = True
    presentation_enabled: bool = False
    presentation_student_id: int = 0
    presentation_teacher_id: int = 0
    database_url: str = ""
    auth_secret: SecretStr = SecretStr("")
    token_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    groq_api_key: SecretStr = SecretStr("")
    groq_text_model: str = "openai/gpt-oss-120b"
    groq_audio_model: str = "whisper-large-v3"
    media_dir: Path = ROOT / ".media"
    ffmpeg_path: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
