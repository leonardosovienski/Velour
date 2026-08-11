import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_list(value: str | None, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if not value:
        return default
    return tuple(item.strip().rstrip("/") for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str
    secret_key: str
    jwt_algorithm: str
    token_expire_minutes: int
    cors_origins: tuple[str, ...]
    upload_dir: Path
    scheduler_enabled: bool
    auto_create_tables: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_use_tls: bool


@lru_cache
def get_settings() -> Settings:
    environment = os.getenv("APP_ENV", "development").strip().lower()
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key:
        raise RuntimeError("SECRET_KEY não configurada. Defina a variável antes de iniciar o servidor.")
    if environment == "production" and len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY deve ter pelo menos 32 caracteres em produção.")

    database_url = os.getenv("DATABASE_URL", "sqlite:///./velour.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    default_origins = ("http://localhost:5173", "http://127.0.0.1:5173")
    origins = _as_list(os.getenv("CORS_ORIGINS"), default_origins)
    if environment == "production" and not os.getenv("CORS_ORIGINS"):
        raise RuntimeError("CORS_ORIGINS deve ser configurada em produção.")

    return Settings(
        environment=environment,
        database_url=database_url,
        secret_key=secret_key,
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        token_expire_minutes=int(os.getenv("TOKEN_EXPIRE_MINUTES", "480")),
        cors_origins=origins,
        upload_dir=Path(os.getenv("UPLOAD_DIR", "./uploads")).resolve(),
        scheduler_enabled=_as_bool(os.getenv("SCHEDULER_ENABLED"), True),
        auto_create_tables=_as_bool(os.getenv("AUTO_CREATE_TABLES"), environment != "production"),
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_from=os.getenv("SMTP_FROM", ""),
        smtp_use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), True),
    )


settings = get_settings()
