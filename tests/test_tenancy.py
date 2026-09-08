from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import create_access_token
from config import settings
from database import Base, ScopedSession, get_db, system_scope, tenant_scope
from main import app
from models import Appointment, User, UserRole
from tests.tenancy_helpers import (
    seed_two_tenants, assert_read_isolation, assert_bulk_isolation, assert_fail_closed,
    assert_write_isolation, assert_database_constraints,
)


@pytest.fixture
def isolated_accounts():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, class_=ScopedSession, autoflush=False)
    accounts = seed_two_tenants(factory)
    yield factory, accounts
    engine.dispose()


@pytest.mark.parametrize("assertion", [assert_read_isolation, assert_bulk_isolation, assert_fail_closed,
                                       assert_write_isolation, assert_database_constraints])
def test_tenant_session_boundary(isolated_accounts, assertion):
    assertion(*isolated_accounts)


@pytest.fixture
def tenant_api(isolated_accounts, monkeypatch):
    factory, accounts = isolated_accounts
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    monkeypatch.setattr("audit.SessionLocal", factory)
    with TestClient(app) as api:
        yield api, factory, accounts
    app.dependency_overrides.pop(get_db, None)


def headers(account):
    return {"Authorization": "Bearer " + create_access_token(account["user"], account["email"], "admin", tenant_id=account["tenant"])}


def test_http_idor_lists_writes_and_global_email_conflict(tenant_api):
    api, factory, (a, b) = tenant_api
    auth = headers(a)
    assert [row["id"] for row in api.get("/clients", headers=auth).json()] == [a["client"]]
    for path in (f"/clients/{b['client']}", f"/appointments/{b['appointment']}"):
        assert api.get(path, headers=auth).status_code == 404
    assert api.patch(f"/users/{b['user']}", headers=auth, json={"name": "Stolen"}).status_code == 404
    assert api.post("/appointments", headers=auth, json={
        "client_id": b["client"], "service_id": a["service"], "professional_id": a["professional"],
        "scheduled_at": "2030-02-01T10:00:00",
    }).status_code == 404
    assert api.post("/users", headers=auth, json={"name": "Duplicate", "email": b["email"],
        "password": "long-test-password", "role": "manager"}).status_code == 409
    assert api.get("/auth/me", headers=auth).json()["tenant_id"] == a["tenant"]


def test_invalid_tenant_and_revoked_tokens_are_unauthorized(tenant_api):
    api, factory, (a, b) = tenant_api
    for identity in (None, b["tenant"], "1", -1):
        token = create_access_token(a["user"], a["email"], "admin", tenant_id=identity)
        assert api.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    malformed = jwt.encode({"sub": "oops", "tenant_id": a["tenant"], "exp": datetime.now(timezone.utc) + timedelta(minutes=1)}, settings.secret_key, algorithm=settings.jwt_algorithm)
    assert api.get("/auth/me", headers={"Authorization": f"Bearer {malformed}"}).status_code == 401
    with factory() as db:
        tenant_scope(db, a["tenant"])
        db.get(User, a["user"]).token_version += 1
        db.commit()
    assert api.get("/auth/me", headers=headers(a)).status_code == 401


def test_photos_require_tenant_and_professional_ownership(tenant_api, tmp_path, monkeypatch):
    api, factory, (a, b) = tenant_api
    monkeypatch.setattr("main.UPLOAD_ROOT", tmp_path)
    name = "private-photo.jpg"
    (tmp_path / name).write_bytes(b"\xff\xd8\xffsome-image")
    with factory() as db:
        tenant_scope(db, b["tenant"])
        db.get(Appointment, b["appointment"]).photo_before_url = f"/uploads/{name}"
        db.commit()
    assert api.get(f"/uploads/{name}", headers=headers(a)).status_code == 404
    assert api.get(f"/uploads/{name}", headers=headers(b)).status_code == 200
    laundering = api.post(f"/appointments/{a['appointment']}/complete", headers=headers(a),
                         json={"price_charged": 100, "photo_before_url": f"/uploads/{name}"})
    assert laundering.status_code == 422
    # A professional in the same tenant still cannot read another professional's photo.
    with factory() as db:
        tenant_scope(db, b["tenant"])
        user = db.get(User, b["user"])
        user.role = UserRole.professional
        user.professional_id = None
        db.commit()
    assert api.get(f"/uploads/{name}", headers=headers(b)).status_code == 403
