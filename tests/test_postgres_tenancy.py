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


def test_migrated_postgresql_business_dashboard(postgres_accounts):
    """Run the actual birthday SQL, professional KPIs and zero-price reports."""
    from datetime import datetime, timedelta
    from decimal import Decimal

    from database import tenant_scope
    from models import Appointment, AppointmentStatus, Client, User, UserRole
    from routers.dashboard import alerts, kpis, today_summary, weekly_revenue
    from routers.professionals import professional_dashboard, professional_stats
    from routers.reports import client_report, loyalty_monthly, referrals_monthly, revenue_report

    factory, accounts = postgres_accounts
    when = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    for account in accounts:
        with factory() as db:
            tenant_scope(db, account["tenant"])
            client = db.get(Client, account["client"])
            client.birthdate = when.date().replace(year=2000)
            appointment = db.get(Appointment, account["appointment"])
            appointment.scheduled_at = when
            appointment.ends_at = when + timedelta(hours=1)
            appointment.status = AppointmentStatus.completed
            appointment.price_charged = Decimal("0.00")
            db.commit()

    account = accounts[0]
    with factory() as db:
        tenant_scope(db, account["tenant"])
        user = User(role=UserRole.professional, professional_id=account["professional"])
        birthdays = alerts(db=db, _=user)["birthdays_today"]
        assert [client["id"] for client in birthdays] == [account["client"]]
        assert today_summary(db=db, _=user)["revenue_today"] == 0
        metrics = kpis(period="day", db=db, _=user)
        assert metrics["active_clients"] == metrics["completed_appointments"] == 1
        assert metrics["revenue"] == 0
        assert all(day["revenue"] == 0 for day in weekly_revenue(db=db, _=user))
        assert professional_stats(account["professional"], db=db, _=user)["commission_this_month"] == 0
        assert professional_dashboard(account["professional"], db=db, _=user)["monthly_goal"]["revenue"] == 0
        report = revenue_report(db=db, _=None)
        assert report["total_revenue"] == 0
        assert report["total_appointments"] == 1
        assert client_report(db=db, _=None)["total_active"] == 1
        assert loyalty_monthly(months=1, db=db, _=None)[0]["points_issued"] == 0
        assert referrals_monthly(months=1, db=db, _=None)[0]["referrals_created"] == 0
