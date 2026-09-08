import os
import subprocess
import sys


def _run_config(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    process_env = os.environ.copy()
    for key in ("APP_URL", "FRONTEND_URL", "SIGNUP_ENABLED", "AUTO_CREATE_TABLES", "TERMS_URL", "PRIVACY_URL"):
        process_env.pop(key, None)
    process_env.update(env)
    return subprocess.run(
        [sys.executable, "-c", "from config import settings; print(settings.database_url)"],
        capture_output=True,
        text=True,
        env=process_env,
        check=False,
    )


def test_production_requires_explicit_cors():
    env = {
        "APP_ENV": "production",
        "SECRET_KEY": "x" * 32,
        "CORS_ORIGINS": "",
    }
    result = _run_config(env)
    assert result.returncode != 0
    assert "CORS_ORIGINS" in result.stderr


def test_production_requires_strong_secret():
    env = {
        "APP_ENV": "production",
        "SECRET_KEY": "short",
        "CORS_ORIGINS": "https://app.example.com",
    }
    result = _run_config(env)
    assert result.returncode != 0
    assert "32 caracteres" in result.stderr


def test_normalizes_managed_postgres_url():
    env = {
        "APP_ENV": "production",
        "SECRET_KEY": "x" * 32,
        "CORS_ORIGINS": "https://app.example.com",
        "DATABASE_URL": "postgres://user:pass@db/velour",
    }
    result = _run_config(env)
    assert result.returncode == 0
    assert "postgresql+psycopg://user:pass@db/velour" in result.stdout


def test_production_rejects_sqlite():
    result = _run_config({"APP_ENV": "production", "SECRET_KEY": "x" * 32,
                          "CORS_ORIGINS": "https://app.example.com", "DATABASE_URL": "sqlite:///local.db"})
    assert result.returncode != 0
    assert "PostgreSQL" in result.stderr


def test_production_rejects_public_signup_without_legal_documents():
    result = _run_config({"APP_ENV": "production", "SECRET_KEY": "x" * 32,
                          "CORS_ORIGINS": "https://app.example.com", "DATABASE_URL": "postgres://user:pass@db/velour",
                          "SIGNUP_ENABLED": "true"})
    assert result.returncode != 0
    assert "TERMS_URL" in result.stderr


def test_production_rejects_wildcard_cors():
    result = _run_config({"APP_ENV": "production", "SECRET_KEY": "x" * 32,
                          "CORS_ORIGINS": "*", "DATABASE_URL": "postgres://user:pass@db/velour"})
    assert result.returncode != 0
    assert "CORS_ORIGINS" in result.stderr
