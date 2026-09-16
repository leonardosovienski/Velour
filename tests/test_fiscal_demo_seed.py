import json
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import create_engine, text


def test_demo_seed_requires_empty_database_and_preserves_existing_data(tmp_path):
    root = Path(__file__).resolve().parents[1]
    url = f"sqlite:///{tmp_path / 'demo.db'}"
    env = {**os.environ, "APP_ENV": "development", "FISCAL_MODE": "demo", "DATABASE_URL": url,
           "AUTO_CREATE_TABLES": "false", "SCHEDULER_ENABLED": "false", "PYTHONIOENCODING": "utf-8"}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=root, env=env, check=True, capture_output=True)
    result = subprocess.run([sys.executable, "demo_fiscal.py"], cwd=root, env=env, check=True, capture_output=True)
    access = json.loads(result.stdout)
    assert len(access["password"]) >= 20
    engine = create_engine(url)
    with engine.connect() as connection:
        before = connection.execute(text("SELECT id, status, amount FROM fiscal_documents ORDER BY id")).all()
        assert len(before) == 4
    second = subprocess.run([sys.executable, "demo_fiscal.py"], cwd=root, env=env, capture_output=True)
    assert second.returncode != 0
    with engine.connect() as connection:
        assert connection.execute(text("SELECT id, status, amount FROM fiscal_documents ORDER BY id")).all() == before
    engine.dispose()
