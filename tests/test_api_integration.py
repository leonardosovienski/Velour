"""Testes de integração HTTP fim-a-fim via TestClient (diferente dos demais
arquivos, que testam funções de negócio isoladas). Cobrem autenticação,
autorização por role e o conflito de agenda através da API real."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import hash_password
from database import Base, get_db
from main import app
from models.user import User, UserRole
from tests.conftest import make_client, make_professional, make_category, make_service


@pytest.fixture
def db():
    """Sobrescreve o fixture `db` do conftest com StaticPool: o TestClient
    despacha os endpoints síncronos em outra thread (run_in_threadpool), e
    sqlite:///:memory: com o pool padrão isola um banco por thread — a
    requisição veria um banco vazio, sem tabelas, sem StaticPool aqui."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def api(db, test_client):
    """Redireciona as dependências get_db do app para a sessão de teste (SQLite em memória)."""
    def _override():
        yield db
    app.dependency_overrides[get_db] = _override
    yield test_client
    app.dependency_overrides.pop(get_db, None)


def make_user(db, email="user@velour.com", password="senha123", role=UserRole.professional):
    user = User(name="Usuário Teste", email=email, hashed_password=hash_password(password), role=role)
    db.add(user)
    db.commit()
    return user


def test_login_retorna_token_valido(db, api):
    make_user(db, email="admin@teste.com", password="senha123", role=UserRole.admin)

    resp = api.post("/auth/login", data={"username": "admin@teste.com", "password": "senha123"})

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_credenciais_invalidas_retorna_401(db, api):
    make_user(db, email="admin2@teste.com", password="senha123", role=UserRole.admin)

    resp = api.post("/auth/login", data={"username": "admin2@teste.com", "password": "errada"})

    assert resp.status_code == 401


def test_endpoint_protegido_sem_token_retorna_401(db, api):
    resp = api.get("/clients")
    assert resp.status_code == 401


def test_role_errada_retorna_403(db, api):
    make_user(db, email="prof@teste.com", password="senha123", role=UserRole.professional)
    login = api.post("/auth/login", data={"username": "prof@teste.com", "password": "senha123"})
    token = login.json()["access_token"]

    # /users é restrito a admin/manager (require_admin)
    resp = api.get("/users", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 403


def test_login_rate_limit_apos_5_tentativas_retorna_429(db, api):
    make_user(db, email="ratelimit@teste.com", password="senha123", role=UserRole.admin)

    for _ in range(5):
        resp = api.post("/auth/login", data={"username": "ratelimit@teste.com", "password": "errada"})
        assert resp.status_code == 401

    bloqueado = api.post("/auth/login", data={"username": "ratelimit@teste.com", "password": "errada"})
    assert bloqueado.status_code == 429

    # mesmo com a senha certa, a cota já foi consumida pelas tentativas erradas
    ainda_bloqueado = api.post("/auth/login", data={"username": "ratelimit@teste.com", "password": "senha123"})
    assert ainda_bloqueado.status_code == 429


def test_conflito_de_agenda_retorna_409(db, api):
    make_user(db, email="admin3@teste.com", password="senha123", role=UserRole.admin)
    login = api.post("/auth/login", data={"username": "admin3@teste.com", "password": "senha123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client = make_client(db, name="Cliente API", referral_code="APIREF01", code="VLR-API01")
    prof = make_professional(db, name="Prof API")
    cat = make_category(db)
    svc = make_service(db, cat.id, duration_minutes=60)
    db.commit()

    horario = (datetime(2027, 3, 10, 14, 0)).isoformat()
    payload = {
        "client_id": client.id,
        "professional_id": prof.id,
        "service_id": svc.id,
        "scheduled_at": horario,
    }

    primeiro = api.post("/appointments", json=payload, headers=headers)
    assert primeiro.status_code == 201

    segundo = api.post("/appointments", json=payload, headers=headers)
    assert segundo.status_code == 409


def test_complete_appointment_com_pagamento(db, api):
    make_user(db, email="admin4@teste.com", password="senha123", role=UserRole.admin)
    login = api.post("/auth/login", data={"username": "admin4@teste.com", "password": "senha123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client = make_client(db, name="Cliente Pagto", referral_code="PAYREF01", code="VLR-PAY01")
    prof = make_professional(db, name="Prof Pagto")
    cat = make_category(db)
    svc = make_service(db, cat.id, duration_minutes=30, price=100)
    db.commit()

    horario = datetime(2027, 4, 10, 10, 0).isoformat()
    created = api.post("/appointments", json={
        "client_id": client.id,
        "professional_id": prof.id,
        "service_id": svc.id,
        "scheduled_at": horario,
    }, headers=headers)
    assert created.status_code == 201
    appt_id = created.json()["id"]

    sem_metodo = api.post(f"/appointments/{appt_id}/complete", json={
        "price_charged": 100,
        "paid": True,
    }, headers=headers)
    assert sem_metodo.status_code == 422

    resp = api.post(f"/appointments/{appt_id}/complete", json={
        "price_charged": 100,
        "paid": True,
        "amount_paid": 100,
        "payment_method": "pix",
    }, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["paid"] is True
    assert body["payment_method"] == "pix"
    assert float(body["amount_paid"]) == 100.0


def test_create_appointment_rate_limit_apos_30_por_minuto(db, api):
    from routers.appointments import _create_limiter
    _create_limiter._hits.clear()

    make_user(db, email="admin5@teste.com", password="senha123", role=UserRole.admin)
    login = api.post("/auth/login", data={"username": "admin5@teste.com", "password": "senha123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    prof = make_professional(db, name="Prof RateLimit")
    cat = make_category(db)
    svc = make_service(db, cat.id, duration_minutes=10)
    db.commit()

    for i in range(30):
        client = make_client(db, name=f"Cliente RL {i}", referral_code=f"RLREF{i:03d}", code=f"VLR-RL{i:03d}")
        db.commit()
        horario = datetime(2027, 5, 1, 8, 0) + timedelta(minutes=10 * i)
        resp = api.post("/appointments", json={
            "client_id": client.id,
            "professional_id": prof.id,
            "service_id": svc.id,
            "scheduled_at": horario.isoformat(),
        }, headers=headers)
        assert resp.status_code == 201

    client_extra = make_client(db, name="Cliente Extra", referral_code="RLREFEXTRA", code="VLR-RLEXTRA")
    db.commit()
    bloqueado = api.post("/appointments", json={
        "client_id": client_extra.id,
        "professional_id": prof.id,
        "service_id": svc.id,
        "scheduled_at": (datetime(2027, 5, 1, 8, 0) + timedelta(minutes=10 * 30)).isoformat(),
    }, headers=headers)
    assert bloqueado.status_code == 429
