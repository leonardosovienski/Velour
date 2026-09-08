"""HTTP regressions for professional privacy inside and across salons."""
from datetime import datetime, timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import create_access_token
from database import Base, ScopedSession, get_db, tenant_scope
from models import Appointment, Client, LoyaltyTransaction, Professional, User, UserRole
from models.loyalty import TransactionType
from routers import loyalty, professionals
from routers.billing import require_active_subscription
from tests.tenancy_helpers import seed_two_tenants


@pytest.fixture
def professional_api():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, class_=ScopedSession, autoflush=False)
    own, foreign = seed_two_tenants(factory)
    with factory() as db:
        tenant_scope(db, own["tenant"])
        peer = Professional(name="Outro profissional", specialty="Corte", phone="11999999999", gender="F")
        hidden = Client(name="Cliente de outro profissional", code="VLR-00002", referral_code="OTHERREF",
                        phone="11999999999", gender="F")
        db.add_all([peer, hidden])
        db.flush()
        peer_id, hidden_id = peer.id, hidden.id
        # Several appointments with the same client must not duplicate points
        # transactions or change pagination when applying the access boundary.
        start = datetime(2030, 1, 2, 10)
        db.add_all([
            Appointment(client_id=own["client"], professional_id=own["professional"], service_id=own["service"],
                        scheduled_at=start, ends_at=start + timedelta(hours=1)),
            Appointment(client_id=hidden.id, professional_id=peer.id, service_id=own["service"],
                        scheduled_at=start, ends_at=start + timedelta(hours=1)),
        ])
        for client_id, points in ((own["client"], 100), (own["client"], 50), (hidden.id, 900)):
            db.add(LoyaltyTransaction(client_id=client_id, points=points, type=TransactionType.earned_birthday,
                                     description="Saldo de fidelidade", created_at=start + timedelta(seconds=points)))
        users = {
            "admin": db.get(User, own["user"]),
            "manager": User(name="Gerente", email="manager@test.example", hashed_password="unused", role=UserRole.manager),
            "professional": User(name="Profissional", email="professional@test.example", hashed_password="unused",
                                 role=UserRole.professional, professional_id=own["professional"]),
            "unlinked": User(name="Legado sem vínculo", email="unlinked@test.example", hashed_password="unused",
                             role=UserRole.professional),
        }
        db.add_all(users.values())
        db.commit()
        headers = {name: {"Authorization": "Bearer " + create_access_token(
            user.id, user.email, user.role.value, tenant_id=own["tenant"], token_version=user.token_version,
        )} for name, user in users.items()}
    with factory() as db:
        tenant_scope(db, foreign["tenant"])
        db.add(LoyaltyTransaction(client_id=foreign["client"], points=9999,
                                 type=TransactionType.earned_birthday, description="Outro salão"))
        db.commit()

    app = FastAPI()
    for router in (professionals.router, loyalty.router):
        app.include_router(router, dependencies=[Depends(require_active_subscription)])

    def override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override
    with TestClient(app) as api:
        yield api, headers, own, foreign, peer_id, hidden_id
    engine.dispose()


def test_professional_list_does_not_expose_peers_financial_profiles(professional_api):
    api, headers, own, foreign, peer_id, _ = professional_api
    response = api.get("/professionals", headers=headers["professional"])
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [own["professional"]]
    assert api.get(f"/professionals/{peer_id}", headers=headers["professional"]).status_code == 403
    assert api.get("/professionals?is_active=false", headers=headers["professional"]).json() == []


@pytest.mark.parametrize("role", ["admin", "manager"])
def test_staff_can_list_all_professionals_of_their_salon(professional_api, role):
    api, headers, own, foreign, peer_id, _ = professional_api
    response = api.get("/professionals", headers=headers[role])
    assert response.status_code == 200
    assert {row["id"] for row in response.json()} == {own["professional"], peer_id}
    assert foreign["professional"] not in {row["id"] for row in response.json()}


def test_professional_loyalty_is_limited_to_related_clients_before_pagination(professional_api):
    api, headers, own, foreign, _, hidden_id = professional_api
    auth = headers["professional"]
    response = api.get("/loyalty/transactions", headers=auth)
    assert response.status_code == 200
    assert [row["points"] for row in response.json()] == [100, 50]
    assert {row["client_id"] for row in response.json()} == {own["client"]}
    assert api.get(f"/loyalty/transactions?client_id={hidden_id}", headers=auth).json() == []
    assert api.get(f"/loyalty/transactions?client_id={foreign['client']}", headers=auth).json() == []
    page = api.get("/loyalty/transactions?limit=1&offset=1&type=earned_birthday", headers=auth)
    assert page.status_code == 200
    assert [row["points"] for row in page.json()] == [50]


@pytest.mark.parametrize("role", ["admin", "manager"])
def test_staff_can_see_tenant_loyalty_without_foreign_transactions(professional_api, role):
    api, headers, own, foreign, _, hidden_id = professional_api
    response = api.get("/loyalty/transactions", headers=headers[role])
    assert response.status_code == 200
    assert {row["client_id"] for row in response.json()} == {own["client"], hidden_id}
    assert sum(row["points"] for row in response.json()) == 1050
    assert api.get(f"/loyalty/transactions?client_id={foreign['client']}", headers=headers[role]).json() == []


def test_legacy_professional_without_link_cannot_list_private_records(professional_api):
    api, headers, *_ = professional_api
    for path in ("/professionals", "/loyalty/transactions"):
        response = api.get(path, headers=headers["unlinked"])
        assert response.status_code == 200
        assert response.json() == []
