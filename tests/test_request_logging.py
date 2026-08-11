import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from auth import create_access_token
from request_logging import RequestLoggingMiddleware, _user_id_from_request


def _build_app():
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ok")
    def ok():
        return {"status": "ok"}

    @app.get("/boom")
    def boom():
        raise HTTPException(status_code=404, detail="não encontrado")

    @app.get("/explode")
    def explode():
        raise RuntimeError("erro inesperado")

    return app


@pytest.fixture
def client():
    with TestClient(_build_app(), raise_server_exceptions=False) as c:
        yield c


def test_loga_requisicao_bem_sucedida_em_info(client, caplog):
    with caplog.at_level(logging.INFO, logger="velour.request"):
        resp = client.get("/ok")
    assert resp.status_code == 200
    record = next(r for r in caplog.records if r.message == "request_completed")
    assert record.levelno == logging.INFO
    assert record.extra_fields["status_code"] == 200
    assert record.extra_fields["path"] == "/ok"


def test_loga_erro_4xx_em_warning(client, caplog):
    with caplog.at_level(logging.INFO, logger="velour.request"):
        resp = client.get("/boom")
    assert resp.status_code == 404
    record = next(r for r in caplog.records if r.message == "request_completed")
    assert record.levelno == logging.WARNING


def test_loga_excecao_nao_tratada_e_repropaga(client, caplog):
    with caplog.at_level(logging.INFO, logger="velour.request"):
        resp = client.get("/explode")
    assert resp.status_code == 500
    record = next(r for r in caplog.records if r.message == "unhandled_exception")
    assert record.levelno == logging.ERROR


def test_user_id_from_request_com_token_valido():
    token = create_access_token(7, "user@teste.com", "admin")

    class FakeRequest:
        headers = {"authorization": f"Bearer {token}"}

    assert _user_id_from_request(FakeRequest()) == 7


def test_user_id_from_request_sem_header():
    class FakeRequest:
        headers = {}

    assert _user_id_from_request(FakeRequest()) is None


def test_user_id_from_request_token_invalido():
    class FakeRequest:
        headers = {"authorization": "Bearer token-invalido"}

    assert _user_id_from_request(FakeRequest()) is None
