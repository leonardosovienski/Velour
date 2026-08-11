import pytest
from fastapi import HTTPException

from rate_limit import RateLimiter, request_key


def test_check_permite_ate_o_limite():
    limiter = RateLimiter(max_attempts=3, window_seconds=60, message="limite atingido")
    for _ in range(3):
        limiter.check("chave")
        limiter.record("chave")


def test_check_bloqueia_apos_o_limite():
    limiter = RateLimiter(max_attempts=3, window_seconds=60, message="limite atingido")
    for _ in range(3):
        limiter.check_and_record("chave")

    with pytest.raises(HTTPException) as exc_info:
        limiter.check("chave")
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "limite atingido"


def test_chaves_diferentes_tem_cotas_independentes():
    limiter = RateLimiter(max_attempts=1, window_seconds=60, message="limite atingido")
    limiter.check_and_record("chave-a")
    # chave diferente não deve ser afetada
    limiter.check("chave-b")


def test_check_expira_janela_antiga(monkeypatch):
    import time as time_module

    limiter = RateLimiter(max_attempts=1, window_seconds=1, message="limite atingido")
    limiter.check_and_record("chave")
    with pytest.raises(HTTPException):
        limiter.check("chave")

    # Simula passagem de tempo além da janela: a marca antiga expira
    real_monotonic = time_module.monotonic
    monkeypatch.setattr("rate_limit.time.monotonic", lambda: real_monotonic() + 10)
    limiter.check("chave")  # não deve levantar


def test_request_key_usa_ip_e_user_id():
    class FakeClient:
        host = "1.2.3.4"

    class FakeRequest:
        client = FakeClient()

    class FakeUser:
        id = 42

    assert request_key(FakeRequest(), FakeUser()) == "1.2.3.4:42"
    assert request_key(FakeRequest(), None) == "1.2.3.4"


def test_request_key_sem_client_usa_unknown():
    class FakeRequest:
        client = None

    assert request_key(FakeRequest()) == "unknown"
