from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from rate_limit import RateLimiter
from runtime_guard import RuntimeGuard


def test_concurrent_rate_limit_is_atomic():
    limiter = RateLimiter(5, 60, "limite")
    def attempt(_):
        try:
            limiter.check_and_record("same-user")
            return True
        except HTTPException as error:
            assert error.status_code == 429
            assert int(error.headers["Retry-After"]) > 0
            return False
    with ThreadPoolExecutor(max_workers=20) as executor:
        assert sum(executor.map(attempt, range(100))) == 5


def test_limiter_bounds_untrusted_keys():
    limiter = RateLimiter(1, 60, "limite")
    limiter.max_keys = 2
    limiter.check_and_record("a")
    limiter.check_and_record("b")
    with pytest.raises(HTTPException):
        limiter.check_and_record("c")


def test_second_runtime_refuses_to_start():
    engine = MagicMock()
    engine.connect.return_value.execute.return_value.scalar_one.return_value = False
    guard = RuntimeGuard()
    with pytest.raises(RuntimeError, match="Outra API"):
        guard.acquire(engine)
    engine.connect.return_value.close.assert_called_once()
    assert guard.connection is None


def test_lost_runtime_lease_does_not_reconnect():
    guard = RuntimeGuard()
    guard.connection = MagicMock(invalidated=True)
    with pytest.raises(RuntimeError, match="Lease"):
        guard.check()
    guard.connection.execute.assert_not_called()


def test_private_response_security_headers_and_body_limit():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from security_headers import SecurityHeadersMiddleware
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    @app.get("/private")
    def private():
        return {"private": True}
    with TestClient(app) as client:
        response = client.get("/private")
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert client.post("/private", headers={"content-length": str(12 * 1024 * 1024)}).status_code == 413


def test_support_suspension_revokes_only_target_tenant(db):
    from auth import hash_password
    from database import system_scope
    from models import Tenant, User
    from platform_admin import set_availability
    with system_scope(db):
        other = Tenant(name="Other", slug="other", subscription_status="active")
        db.add(other)
        db.flush()
        user = User(tenant_id=other.id, name="Other admin", email="support-test@example.com",
                    hashed_password=hash_password("safe-test-password"), role="admin", token_version=0)
        db.add(user)
        db.commit()
        original = db.query(Tenant).filter(Tenant.id != other.id).first()
        assert original is not None
        original_active = original.is_active
        with pytest.raises(ValueError, match="slug"):
            set_availability(db, other.id, active=False, confirm_slug="wrong", reason="Test")
        set_availability(db, other.id, active=False, confirm_slug=other.slug, reason="Test suspension")
        db.refresh(user)
        assert user.token_version == 1
        assert not other.is_active
        assert original.is_active == original_active
        assert other.subscription_status == "active"
