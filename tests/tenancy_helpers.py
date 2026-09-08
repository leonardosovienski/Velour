"""The same isolation assertions run against SQLite and migrated PostgreSQL."""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased, joinedload, selectinload

from auth import hash_password
from database import TenantIsolationError, system_scope, tenant_scope
from models import Appointment, BillingWebhookEvent, Client, Professional, Service, ServiceCategory, Tenant, User, UserRole


def seed_two_tenants(factory):
    result = []
    for name in ("Alpha", "Beta"):
        with factory() as db, system_scope(db):
            tenant = Tenant(name=name, slug=f"{name.lower()}-{uuid4().hex}",
                trial_ends_at=datetime.utcnow() + timedelta(days=14))
            db.add(tenant)
            db.commit()
            tenant_id = tenant.id
        with factory() as db:
            tenant_scope(db, tenant_id)
            user = User(name=f"{name} admin", email=f"{uuid4().hex}@example.com",
                hashed_password=hash_password("long-test-password"), role=UserRole.admin)
            client = Client(name=f"{name} client", code="VLR-00001", referral_code="SAMECODE", phone="11999999999", gender="F")
            prof = Professional(name=f"{name} professional", specialty="Hair", phone="11888888888", gender="F")
            category = ServiceCategory(name=f"{name} category")
            db.add_all([user, client, prof, category])
            db.flush()
            service = Service(category_id=category.id, name=f"{name} service", duration_minutes=60, price=100 if name == "Alpha" else 900)
            db.add(service)
            db.flush()
            appt = Appointment(client_id=client.id, professional_id=prof.id, service_id=service.id,
                scheduled_at=datetime(2030, 1, 1, 10), ends_at=datetime(2030, 1, 1, 11), price_charged=service.price)
            db.add(appt)
            db.commit()
            result.append({"tenant": tenant_id, "user": user.id, "email": user.email, "client": client.id,
                           "professional": prof.id, "category": category.id, "service": service.id, "appointment": appt.id})
    return result


def assert_read_isolation(factory, accounts):
    a, b = accounts
    for account, expected_price in ((a, 100), (b, 900)):
        other = b if account == a else a
        with factory() as db:
            tenant_scope(db, account["tenant"])
            assert db.query(Client).count() == 1
            assert db.query(func.count(Client.id)).scalar() == 1
            assert db.query(func.sum(Appointment.price_charged)).scalar() == expected_price
            assert db.query(Client.id).all() == [(account["client"],)]
            client_alias = aliased(Client)
            assert db.query(client_alias).count() == 1
            assert db.query(client_alias.id).all() == [(account["client"],)]
            assert db.query(Appointment.id).join(Client, Client.id == Appointment.client_id).all() == [(account["appointment"],)]
            assert db.get(Client, other["client"]) is None
            assert db.query(Tenant.id).all() == [(account["tenant"],)]
            appt = db.query(Appointment).options(joinedload(Appointment.client), selectinload(Appointment.service)).one()
            assert appt.client.id == account["client"]
            assert appt.service.id == account["service"]
            assert appt.professional.id == account["professional"]
            assert appt.client.appointments == [appt]


def assert_bulk_isolation(factory, accounts):
    a, b = accounts
    with factory() as db:
        tenant_scope(db, a["tenant"])
        assert db.execute(update(Client).values(name="Changed")).rowcount == 1
        db.commit()
        assert db.query(Client).filter(Client.id == b["client"]).update({"phone": "x"}) == 0
        assert db.execute(delete(Appointment).where(Appointment.id == b["appointment"])).rowcount == 0
        for stmt in (update(Client).values(tenant_id=b["tenant"]), update(Client).values(referred_by_id=b["client"]),
                     update(Client).ordered_values((Client.tenant_id, b["tenant"]))):
            with pytest.raises(TenantIsolationError):
                db.execute(stmt)
        with pytest.raises(TenantIsolationError):
            db.bulk_update_mappings(Client, [{"id": b["client"], "name": "Forbidden"}])
        with pytest.raises(TenantIsolationError):
            db.execute(insert(Client), [{"name": "Forbidden"}])
        db.rollback()
    with factory() as db:
        tenant_scope(db, b["tenant"])
        assert db.get(Client, b["client"]).name == "Beta client"
        assert db.get(Appointment, b["appointment"]) is not None


def assert_fail_closed(factory, accounts):
    a, b = accounts
    with factory() as db:
        for action in (lambda: db.query(Client).all(), lambda: db.get(User, a["user"]),
                       lambda: db.execute(text("SELECT 1"))):
            with pytest.raises(TenantIsolationError):
                action()
        tenant_scope(db, a["tenant"])
        for stmt in (text("SELECT * FROM clients"), select(Client.__table__), select(BillingWebhookEvent),
                     select(Client).from_statement(text("SELECT * FROM clients"))):
            with pytest.raises(TenantIsolationError):
                db.execute(stmt)
        with pytest.raises(TenantIsolationError):
            db.connection()
        with pytest.raises(TenantIsolationError):
            tenant_scope(db, b["tenant"])
        with system_scope(db):
            foreign = db.get(Client, b["client"])
            assert foreign is not None
        assert db.get(Client, b["client"]) is None


def assert_write_isolation(factory, accounts):
    a, b = accounts
    with factory() as db:
        tenant_scope(db, a["tenant"])
        appt = db.get(Appointment, a["appointment"])
        appt.client_id = b["client"]
        with pytest.raises(TenantIsolationError):
            db.flush()
        db.rollback()
        client = db.get(Client, a["client"])
        client.tenant_id = b["tenant"]
        with pytest.raises(TenantIsolationError):
            db.flush()
        db.rollback()
        with system_scope(db):
            foreign = db.get(Client, b["client"])
        db.add(foreign)
        db.delete(foreign)
        with pytest.raises(TenantIsolationError):
            db.flush()
        db.rollback()
        assert db.get(Appointment, a["appointment"]).client_id == a["client"]


def assert_database_constraints(factory, accounts):
    a, b = accounts
    with factory() as db, system_scope(db):
        # Core bypasses ORM event validation intentionally; the DB must stop it.
        with pytest.raises(IntegrityError):
            db.execute(update(Appointment.__table__).where(Appointment.id == a["appointment"]).values(client_id=b["client"]))
        db.rollback()
        assert db.query(Appointment).filter(Appointment.id == a["appointment"]).one().client_id == a["client"]
