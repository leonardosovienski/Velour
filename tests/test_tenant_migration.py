import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect, text


@pytest.mark.parametrize("emails, succeeds", [([" Owner@Example.com "], True), (["Owner@example.com", "owner@example.com"], False)])
def test_legacy_email_normalization_preserves_access_or_stops_before_schema_change(tmp_path, emails, succeeds):
    database_path = tmp_path / "legacy.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{database_path}", "AUTO_CREATE_TABLES": "false", "APP_ENV": "development"}
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "alembic", "upgrade"]
    subprocess.run(command + ["c4f1a9d7e2b0"], cwd=root, env=env, check=True, capture_output=True)
    engine = create_engine(env["DATABASE_URL"])
    with engine.begin() as connection:
        for email in emails:
            connection.execute(text("INSERT INTO users (name,email,hashed_password,role,is_active,created_at) VALUES ('Owner',:email,'legacy-hash','admin',1,CURRENT_TIMESTAMP)"), {"email": email})
    result = subprocess.run(command + ["head"], cwd=root, env=env, capture_output=True)
    assert (result.returncode == 0) == succeeds
    with engine.connect() as connection:
        if succeeds:
            assert connection.execute(text("SELECT email,tenant_id,token_version FROM users")).one() == ("owner@example.com", 1, 0)
            assert connection.execute(text("SELECT COUNT(*) FROM tenants")).scalar_one() == 1
        else:
            assert "tenants" not in inspect(connection).get_table_names()
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "c4f1a9d7e2b0"
    engine.dispose()
