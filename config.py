import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

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
    app_url: str
    signup_enabled: bool
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_id: str
    stripe_livemode: bool
    password_reset_expire_minutes: int
    terms_version: str
    terms_url: str
    privacy_url: str

    @property
    def frontend_url(self) -> str:
        return self.app_url


@lru_cache
def get_settings() -> Settings:
    environment = os.getenv("APP_ENV", "development").strip().lower()
    if environment not in {"development", "test", "production"}:
        raise RuntimeError("APP_ENV deve ser development, test ou production.")
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key:
        raise RuntimeError("SECRET_KEY não configurada. Defina a variável antes de iniciar o servidor.")
    if environment == "production" and len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY deve ter pelo menos 32 caracteres em produção.")
    if environment == "production" and any(part in secret_key.lower() for part in ("troque", "change-me", "example", "ci-only")):
        raise RuntimeError("SECRET_KEY de exemplo não pode ser usada em produção.")

    database_url = os.getenv("DATABASE_URL", "sqlite:///./velour.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    default_origins = ("http://localhost:5173", "http://127.0.0.1:5173")
    origins = _as_list(os.getenv("CORS_ORIGINS"), default_origins)
    if environment == "production" and not os.getenv("CORS_ORIGINS"):
        raise RuntimeError("CORS_ORIGINS deve ser configurada em produção.")

    app_url = os.getenv("APP_URL", os.getenv("FRONTEND_URL", origins[0] if origins else "http://localhost:5173")).rstrip("/")
    signup_enabled = _as_bool(os.getenv("SIGNUP_ENABLED"), environment != "production")
    terms_url = os.getenv("TERMS_URL", "")
    privacy_url = os.getenv("PRIVACY_URL", "")
    auto_create = _as_bool(os.getenv("AUTO_CREATE_TABLES"), environment != "production")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    if algorithm != "HS256":
        raise RuntimeError("JWT_ALGORITHM deve ser HS256.")
    token_minutes = int(os.getenv("TOKEN_EXPIRE_MINUTES", "480"))
    reset_minutes = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30"))
    if not 5 <= token_minutes <= 1440 or not 5 <= reset_minutes <= 60:
        raise RuntimeError("Expiração de token deve ser 5–1440 minutos e recuperação 5–60 minutos.")
    if environment == "production":
        if not database_url.startswith("postgresql+psycopg://"):
            raise RuntimeError("DATABASE_URL deve usar PostgreSQL em produção.")
        if auto_create:
            raise RuntimeError("AUTO_CREATE_TABLES deve ser false em produção; use Alembic.")
        for name, values in (("CORS_ORIGINS", origins), ("APP_URL", (app_url,))):
            for value in values:
                parsed = urlsplit(value)
                if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/") or "*" in value:
                    raise RuntimeError(f"{name} deve conter origens HTTPS explícitas, sem caminho ou curingas.")
        if app_url not in origins:
            raise RuntimeError("APP_URL deve estar em CORS_ORIGINS.")
        if signup_enabled:
            for name, value in (("TERMS_URL", terms_url), ("PRIVACY_URL", privacy_url)):
                parsed = urlsplit(value)
                if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                    raise RuntimeError(f"{name} HTTPS publicada é obrigatória para abrir cadastros.")
            if not os.getenv("SMTP_HOST") or not os.getenv("SMTP_FROM"):
                raise RuntimeError("SMTP_HOST e SMTP_FROM são obrigatórios para recuperação de conta em produção.")
        if os.getenv("SMTP_HOST") and not _as_bool(os.getenv("SMTP_USE_TLS"), True):
            raise RuntimeError("SMTP_USE_TLS deve ser true em produção.")

    return Settings(
        environment=environment,
        database_url=database_url,
        secret_key=secret_key,
        jwt_algorithm=algorithm,
        token_expire_minutes=token_minutes,
        cors_origins=origins,
        upload_dir=Path(os.getenv("UPLOAD_DIR", "./uploads")).resolve(),
        scheduler_enabled=_as_bool(os.getenv("SCHEDULER_ENABLED"), True),
        auto_create_tables=auto_create,
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_from=os.getenv("SMTP_FROM", ""),
        smtp_use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), True),
        app_url=app_url,
        signup_enabled=signup_enabled,
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        stripe_price_id=os.getenv("STRIPE_PRICE_ID", ""),
        stripe_livemode=_as_bool(os.getenv("STRIPE_LIVEMODE"), False),
        password_reset_expire_minutes=reset_minutes,
        terms_version=os.getenv("TERMS_VERSION", "2026-09-08"),
        terms_url=terms_url,
        privacy_url=privacy_url,
    )


settings = get_settings()
