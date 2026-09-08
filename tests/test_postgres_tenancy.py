"""Release gate: run against an Alembic-migrated PostgreSQL database in CI."""
import os

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from database import ScopedSession
from tests.tenancy_helpers import (
    seed_two_tenants, assert_read_isolation, assert_bulk_isolation, assert_fail_closed,
    assert_write_isolation, assert_database_constraints,
)

pytestmark = pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="TEST_POSTGRES_URL not configured")


@pytest.fixture
def postgres_accounts():
    url = os.environ["TEST_POSTGRES_URL"].replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "d9e64a3b2f10"
        connection.rollback()
        transaction = connection.begin()
        factory = sessionmaker(bind=connection, class_=ScopedSession, autoflush=False, join_transaction_mode="create_savepoint")
        accounts = seed_two_tenants(factory)
        try:
            yield factory, accounts
        finally:
            transaction.rollback()
    engine.dispose()


@pytest.mark.parametrize("assertion", [assert_read_isolation, assert_bulk_isolation, assert_fail_closed,
                                       assert_write_isolation, assert_database_constraints])
def test_migrated_postgresql_tenant_boundary(postgres_accounts, assertion):
    assertion(*postgres_accounts)
