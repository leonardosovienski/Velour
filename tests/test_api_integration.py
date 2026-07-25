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
