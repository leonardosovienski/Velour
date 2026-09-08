"""SaaS acceptance/security regressions without external Stripe/SMTP accounts."""
import hashlib
import hmac
import json
import time
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
import stripe
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import create_access_token, hash_password, verify_password
from database import Base, ScopedSession, get_db, system_scope
from models import BillingWebhookEvent, Client, PasswordResetToken, Tenant, User, UserRole
from routers import account_recovery, auth as auth_routes, billing, tenants

REAL_STRIPE_CLIENT = billing._stripe


@pytest.fixture
def saas(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, class_=ScopedSession, expire_on_commit=False)
    app = FastAPI()
    for router in (auth_routes.router, tenants.router, account_recovery.router, billing.router):
        app.include_router(router)

    @app.get("/business", dependencies=[Depends(billing.require_active_subscription)])
    def business():
        return {"ok": True}

    def session_override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = session_override
    for limiter in (tenants._signup_limiter, tenants._export_limiter, account_recovery._recovery_limiter,
                    account_recovery._email_limiter, account_recovery._reset_limiter, billing._session_limiter,
                    auth_routes._login_limiter, auth_routes._login_ip_limiter):
        limiter._hits.clear()
    config = replace(billing.settings, signup_enabled=True, stripe_secret_key="sk_test_mock",
                     stripe_webhook_secret="whsec_test_secret", stripe_price_id="price_monthly",
                     stripe_livemode=False, app_url="https://app.example.com",
                     terms_url="https://example.com/terms", privacy_url="https://example.com/privacy")
    for module in (billing, tenants, account_recovery):
        monkeypatch.setattr(module, "settings", config)
    gateway = MagicMock()
    gateway.v1.customers.create.return_value = {"id": "cus_test"}
    gateway.v1.subscriptions.list.return_value = {"data": [], "has_more": False}
    gateway.v1.checkout.sessions.list.return_value = {"data": [], "has_more": False}
    gateway.v1.prices.retrieve.return_value = {"active": True, "type": "recurring", "livemode": False,
                                              "recurring": {"interval": "month", "interval_count": 1}}
    gateway.v1.checkout.sessions.create.return_value = {"id": "cs_test", "url": "https://checkout.stripe.com/test",
                                                       "expires_at": int(time.time()) + 86400}
    gateway.v1.billing_portal.sessions.create.return_value = {"url": "https://billing.stripe.com/test"}
    monkeypatch.setattr(billing, "_stripe", lambda: gateway)
    with TestClient(app) as client:
        yield client, factory, gateway, config
    Base.metadata.drop_all(engine)
    engine.dispose()


def signup(client, email="owner@example.com", name="Salão Teste"):
    return client.post("/tenants/signup", json={
        "tenant_name": name, "admin_name": "Proprietário", "admin_email": email,
        "admin_password": "secure passphrase 2026", "accepted_terms": True,
    })


def credentials(client, email="owner@example.com"):
    response = signup(client, email)
    assert response.status_code == 201, response.text
    data = response.json()
    return data, {"Authorization": f"Bearer {data['access_token']}"}


def set_tenant(factory, tenant_id, **fields):
    with factory() as db, system_scope(db):
        tenant = db.get(Tenant, tenant_id)
        for name, value in fields.items():
            setattr(tenant, name, value)
        db.commit()


def event(event_id="evt_one", kind="customer.subscription.updated", sub_id="sub_one"):
    return {"id": event_id, "object": "event", "type": kind, "livemode": False,
            "created": int(time.time()), "data": {"object": {"id": sub_id, "customer": "cus_test"}}}


def subscription(tenant_id, status="active", sub_id="sub_one"):
    return {"id": sub_id, "object": "subscription", "customer": "cus_test", "status": status,
            "metadata": {"tenant_id": str(tenant_id)}, "livemode": False,
            "trial_end": int(time.time()) + 86400,
            "latest_invoice": {"created": int(time.time())},
            "items": {"data": [{"price": {"id": "price_monthly"}, "quantity": 1,
                                 "current_period_end": int(time.time()) + 30 * 86400}]}}


def webhook(client, config, payload):
    body = json.dumps(payload).encode()
    timestamp = int(time.time())
    signature = hmac.new(config.stripe_webhook_secret.encode(), str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()
    return client.post("/billing/webhook", content=body, headers={"Stripe-Signature": f"t={timestamp},v1={signature}", "Content-Type": "application/json"})


def test_signup_is_atomic_scoped_normalized_and_records_consent(saas):
    client, factory, _, config = saas
    data, headers = credentials(client, "OWNER@EXAMPLE.COM")
    assert data["role"] == "admin"
    assert client.get("/auth/me", headers=headers).json()["tenant_id"] == data["tenant_id"]
    assert client.get("/business", headers=headers).status_code == 200
    with factory() as db, system_scope(db):
        user = db.query(User).one()
        tenant = db.query(Tenant).one()
        assert user.email == "owner@example.com"
        assert verify_password("secure passphrase 2026", user.hashed_password)
        assert user.tenant_id == tenant.id
        assert tenant.accepted_terms_at and tenant.terms_version == config.terms_version
        remaining = tenant.trial_ends_at - datetime.now(timezone.utc).replace(tzinfo=None)
        assert timedelta(days=13, hours=23) < remaining <= timedelta(days=14)
    assert signup(client).status_code == 409
    with factory() as db, system_scope(db):
        assert db.query(Tenant).count() == db.query(User).count() == 1


def test_signup_needs_consent_long_password_and_config(saas, monkeypatch):
    client, _, _, config = saas
    body = {"tenant_name": "Teste", "admin_name": "Nome", "admin_email": "test@example.com",
            "admin_password": "short", "accepted_terms": False}
    assert client.post("/tenants/signup", json=body).status_code == 422
    body.update(admin_password="long enough passphrase", accepted_terms=True, tenant_id=99)
    assert client.post("/tenants/signup", json=body).status_code == 422
    del body["tenant_id"]
    monkeypatch.setattr(tenants, "settings", replace(config, signup_enabled=False))
    assert client.get("/tenants/signup-config").json()["signup_enabled"] is False
    assert client.post("/tenants/signup", json=body).status_code == 503


def test_signup_rate_limit(saas):
    client, _, _, _ = saas
    for index in range(5):
        assert signup(client, f"owner{index}@example.com").status_code == 201
    assert signup(client, "blocked@example.com").status_code == 429


@pytest.mark.parametrize("status,period,trial,past_due,allowed", [
    ("trialing", None, 1, None, True), ("trialing", None, -1, None, False),
    ("active", 1, None, None, True), ("active", -1, None, None, False),
    ("active", None, None, None, False), ("past_due", None, None, -1, True),
    ("past_due", None, None, -8, False), ("past_due", None, None, None, False),
    ("cancelled", 30, 30, None, False), ("unpaid", 30, None, None, False),
    ("paused", 30, None, None, False), ("unknown", 30, None, None, False),
])
def test_subscription_access_fails_closed(status, period, trial, past_due, allowed):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    shifted = lambda days: now + timedelta(days=days) if days is not None else None
    tenant = Tenant(is_active=True, subscription_status=status, current_period_end=shifted(period),
                    trial_ends_at=shifted(trial), past_due_since=shifted(past_due))
    assert billing.subscription_allows_access(tenant, now) is allowed
    tenant.is_active = False
    assert not billing.subscription_allows_access(tenant, now)


def test_expired_tenant_can_login_check_billing_and_export_scoped_data(saas):
    client, factory, _, _ = saas
    first, headers = credentials(client)
    second, _ = credentials(client, "other@example.com")
    set_tenant(factory, first["tenant_id"], trial_ends_at=datetime(2000, 1, 1))
    with factory() as db, system_scope(db):
        for data, name in ((first, "Own customer"), (second, "Other secret customer")):
            db.add(Client(tenant_id=data["tenant_id"], code=f"C-{data['tenant_id']}", name=name,
                          phone="11999999999", gender="F", referral_code=f"REF{data['tenant_id']}", first_visit=date.today()))
        db.commit()
    assert client.get("/business", headers=headers).status_code == 402
    assert client.get("/auth/me", headers=headers).status_code == 200
    status = client.get("/billing/status", headers=headers).json()
    assert status["subscription_status"] == "expired" and not status["access_allowed"]
    exported = client.get("/tenants/export", headers=headers)
    assert exported.status_code == 200
    assert exported.headers["cache-control"] == "no-store"
    assert "Own customer" in exported.text
    for secret in ("Other secret customer", "hashed_password", "token_version", "password_reset_tokens", "stripe_customer_id"):
        assert secret not in exported.text


def test_manager_cannot_manage_billing_or_export(saas):
    client, factory, gateway, _ = saas
    data, _ = credentials(client)
    with factory() as db, system_scope(db):
        manager = User(name="Manager", email="manager@example.com", role=UserRole.manager,
                       hashed_password=hash_password("manager passphrase"), tenant_id=data["tenant_id"], token_version=0)
        db.add(manager)
        db.flush()
        token = create_access_token(manager.id, manager.email, manager.role.value, tenant_id=manager.tenant_id)
        db.commit()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/billing/status", headers=headers).json()["can_manage_billing"] is False
    assert client.get("/tenants/export", headers=headers).status_code == 403
    assert client.post("/billing/checkout-session", headers=headers).status_code == 403
    assert client.post("/billing/portal-session", headers=headers).status_code == 403
    gateway.v1.checkout.sessions.create.assert_not_called()


def test_checkout_pins_customer_price_redirect_and_preserves_trial(saas):
    client, factory, gateway, config = saas
    data, headers = credentials(client)
    response = client.post("/billing/checkout-session", headers=headers, json={"price": "price_attacker", "tenant_id": 555})
    assert response.status_code == 200, response.text
    params = gateway.v1.checkout.sessions.create.call_args.args[0]
    assert params["customer"] == "cus_test"
    assert params["line_items"] == [{"price": config.stripe_price_id, "quantity": 1}]
    assert params["success_url"] == "https://app.example.com/billing?checkout=success"
    assert params["subscription_data"]["metadata"] == {"tenant_id": str(data["tenant_id"])}
    assert params["subscription_data"]["trial_end"] > time.time() + 13 * 86400
    with factory() as db, system_scope(db):
        tenant = db.get(Tenant, data["tenant_id"])
        assert tenant.stripe_customer_id == "cus_test" and tenant.checkout_session_id == "cs_test"
        assert tenant.subscription_status == "trialing"  # redirects don't activate payment


def test_checkout_late_trial_does_not_charge_early(saas):
    client, factory, gateway, _ = saas
    data, headers = credentials(client)
    set_tenant(factory, data["tenant_id"], trial_ends_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1))
    assert client.post("/billing/checkout-session", headers=headers).status_code == 200
    end = gateway.v1.checkout.sessions.create.call_args.args[0]["subscription_data"]["trial_end"]
    assert end >= time.time() + 48 * 3600


def test_checkout_reuses_open_session_and_blocks_existing_subscription(saas):
    client, factory, gateway, _ = saas
    data, headers = credentials(client)
    set_tenant(factory, data["tenant_id"], stripe_customer_id="cus_test")
    gateway.v1.checkout.sessions.list.return_value = {"data": [{"id": "cs_existing", "mode": "subscription",
        "metadata": {"tenant_id": str(data["tenant_id"])}, "url": "https://checkout.stripe.com/existing", "expires_at": int(time.time()) + 3600}]}
    assert client.post("/billing/checkout-session", headers=headers).json()["url"].endswith("existing")
    gateway.v1.checkout.sessions.create.assert_not_called()
    gateway.v1.subscriptions.list.return_value = {"data": [{"id": "sub_existing", "status": "past_due"}]}
    assert client.post("/billing/checkout-session", headers=headers).status_code == 409
    gateway.v1.checkout.sessions.create.assert_not_called()


def test_checkout_rejects_wrong_live_mode_or_nonmonthly_price(saas):
    client, _, gateway, _ = saas
    _, headers = credentials(client)
    gateway.v1.prices.retrieve.return_value["livemode"] = True
    assert client.post("/billing/checkout-session", headers=headers).status_code == 503
    gateway.v1.prices.retrieve.return_value.update(livemode=False, recurring={"interval": "year", "interval_count": 1})
    assert client.post("/billing/checkout-session", headers=headers).status_code == 503
    gateway.v1.checkout.sessions.create.assert_not_called()


def test_portal_targets_authenticated_tenant_customer(saas):
    client, factory, gateway, _ = saas
    data, headers = credentials(client)
    set_tenant(factory, data["tenant_id"], stripe_customer_id="cus_owner")
    assert client.post("/billing/portal-session", headers=headers, json={"customer": "cus_other"}).status_code == 200
    assert gateway.v1.billing_portal.sessions.create.call_args.args[0] == {
        "customer": "cus_owner", "return_url": "https://app.example.com/billing"}


def test_webhook_signature_mode_and_idempotency(saas):
    client, factory, gateway, config = saas
    data, _ = credentials(client)
    set_tenant(factory, data["tenant_id"], stripe_customer_id="cus_test")
    gateway.v1.subscriptions.retrieve.return_value = subscription(data["tenant_id"])
    assert client.post("/billing/webhook", json=event()).status_code == 400
    wrong_mode = event()
    wrong_mode["livemode"] = True
    assert webhook(client, config, wrong_mode).status_code == 400
    assert webhook(client, config, event()).status_code == 200
    assert webhook(client, config, event()).json()["duplicate"] is True
    gateway.v1.subscriptions.retrieve.assert_called_once()
    with factory() as db, system_scope(db):
        tenant = db.get(Tenant, data["tenant_id"])
        assert tenant.subscription_status == "active" and tenant.stripe_subscription_id == "sub_one"
        assert tenant.current_period_end > datetime.now(timezone.utc).replace(tzinfo=None)
        assert db.query(BillingWebhookEvent).count() == 1


def test_webhook_uses_current_subscription_instead_of_stale_event(saas):
    client, factory, gateway, config = saas
    data, headers = credentials(client)
    set_tenant(factory, data["tenant_id"], stripe_customer_id="cus_test", stripe_subscription_id="sub_one")
    gateway.v1.subscriptions.retrieve.return_value = subscription(data["tenant_id"], "canceled")
    stale = event(kind="checkout.session.completed")
    stale["data"]["object"].update(id="cs_old", subscription="sub_one", payment_status="paid")
    stale["created"] = 100
    assert webhook(client, config, stale).status_code == 200
    assert client.get("/billing/status", headers=headers).json()["subscription_status"] == "cancelled"
    assert client.get("/business", headers=headers).status_code == 402


def test_webhook_old_subscription_cannot_replace_current_subscription(saas):
    client, factory, gateway, config = saas
    data, _ = credentials(client)
    set_tenant(factory, data["tenant_id"], stripe_customer_id="cus_test", stripe_subscription_id="sub_current", subscription_status="active")
    gateway.v1.subscriptions.retrieve.return_value = subscription(data["tenant_id"], sub_id="sub_current")
    assert webhook(client, config, event(sub_id="sub_old")).json()["ignored"] is True
    with factory() as db, system_scope(db):
        assert db.get(Tenant, data["tenant_id"]).stripe_subscription_id == "sub_current"


def test_webhook_failed_api_is_retried_and_unpaid_does_not_activate(saas):
    client, factory, gateway, config = saas
    data, headers = credentials(client)
    set_tenant(factory, data["tenant_id"], stripe_customer_id="cus_test")
    gateway.v1.subscriptions.retrieve.side_effect = stripe.APIConnectionError("temporary")
    assert webhook(client, config, event()).status_code == 502
    with factory() as db, system_scope(db):
        assert db.query(BillingWebhookEvent).count() == 0
    gateway.v1.subscriptions.retrieve.side_effect = None
    gateway.v1.subscriptions.retrieve.return_value = subscription(data["tenant_id"], "unpaid")
    assert webhook(client, config, event()).status_code == 200
    assert client.get("/business", headers=headers).status_code == 402


def test_webhook_cannot_activate_other_tenant_or_unknown_plan(saas):
    client, factory, gateway, config = saas
    data, headers = credentials(client)
    set_tenant(factory, data["tenant_id"], stripe_customer_id="cus_test")
    sub = subscription(99999)
    gateway.v1.subscriptions.retrieve.return_value = sub
    assert webhook(client, config, event()).status_code == 400
    sub["metadata"]["tenant_id"] = str(data["tenant_id"])
    sub["items"]["data"][0]["price"]["id"] = "price_unrelated"
    assert webhook(client, config, event()).status_code == 200
    assert client.get("/billing/status", headers=headers).json()["subscription_status"] == "unsupported_plan"
    assert client.get("/business", headers=headers).status_code == 402


def test_past_due_grace_uses_current_invoice_and_does_not_restart(saas):
    client, factory, gateway, config = saas
    data, _ = credentials(client)
    set_tenant(factory, data["tenant_id"], stripe_customer_id="cus_test")
    sub = subscription(data["tenant_id"], "past_due")
    failure_time = int(time.time()) - 5 * 86400
    sub["latest_invoice"]["created"] = failure_time
    gateway.v1.subscriptions.retrieve.return_value = sub
    stale = event()
    stale["created"] = 100
    assert webhook(client, config, stale).status_code == 200
    with factory() as db, system_scope(db):
        expected = db.get(Tenant, data["tenant_id"]).past_due_since
        assert int(expected.replace(tzinfo=timezone.utc).timestamp()) == failure_time
    sub["latest_invoice"]["created"] = int(time.time())
    assert webhook(client, config, event("evt_two")).status_code == 200
    with factory() as db, system_scope(db):
        assert db.get(Tenant, data["tenant_id"]).past_due_since == expected


def test_password_reset_generic_single_use_hashed_and_revokes_sessions(saas, monkeypatch):
    client, factory, _, _ = saas
    data, headers = credentials(client)
    sent = []
    monkeypatch.setattr(account_recovery, "is_configured", lambda: True)
    monkeypatch.setattr(account_recovery, "send_password_reset", lambda *args: sent.append(args))
    existing = client.post("/auth/forgot-password", json={"email": "owner@example.com"})
    missing = client.post("/auth/forgot-password", json={"email": "missing@example.com"})
    assert existing.status_code == missing.status_code == 200 and existing.json() == missing.json()
    assert len(sent) == 1
    token = sent[0][2]
    with factory() as db, system_scope(db):
        reset = db.query(PasswordResetToken).one()
        assert reset.token_hash == hashlib.sha256(token.encode()).hexdigest()
        assert token not in reset.token_hash and reset.tenant_id == data["tenant_id"]
    body = {"token": token, "new_password": "my new safe passphrase"}
    assert client.post("/auth/reset-password", json=body).status_code == 200
    assert client.post("/auth/reset-password", json=body).status_code == 400
    assert client.get("/auth/me", headers=headers).status_code == 401
    assert client.post("/auth/login", data={"username": "owner@example.com", "password": "secure passphrase 2026"}).status_code == 401
    login = client.post("/auth/login", data={"username": "owner@example.com", "password": "my new safe passphrase"})
    assert login.status_code == 200
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"}).status_code == 200


def test_password_reset_expired_and_superseded_links_rejected(saas, monkeypatch):
    client, factory, _, _ = saas
    credentials(client)
    sent = []
    monkeypatch.setattr(account_recovery, "is_configured", lambda: True)
    monkeypatch.setattr(account_recovery, "send_password_reset", lambda *args: sent.append(args))
    for _ in range(2):
        assert client.post("/auth/forgot-password", json={"email": "owner@example.com"}).status_code == 200
    assert client.post("/auth/reset-password", json={"token": sent[0][2], "new_password": "new long password"}).status_code == 400
    with factory() as db, system_scope(db):
        for token in db.query(PasswordResetToken).all():
            token.expires_at = datetime(2000, 1, 1)
        db.commit()
    assert client.post("/auth/reset-password", json={"token": sent[1][2], "new_password": "new long password"}).status_code == 400


def test_password_recovery_disabled_smtp_and_inactive_accounts(saas, monkeypatch):
    client, factory, _, _ = saas
    data, _ = credentials(client)
    monkeypatch.setattr(account_recovery, "is_configured", lambda: False)
    assert client.post("/auth/forgot-password", json={"email": "owner@example.com"}).status_code == 503
    monkeypatch.setattr(account_recovery, "is_configured", lambda: True)
    send = MagicMock()
    monkeypatch.setattr(account_recovery, "send_password_reset", send)
    set_tenant(factory, data["tenant_id"], is_active=False)
    assert client.post("/auth/forgot-password", json={"email": "owner@example.com"}).status_code == 200
    send.assert_not_called()


def test_missing_stripe_config_is_explicit_and_fails_closed(saas, monkeypatch):
    client, _, gateway, config = saas
    _, headers = credentials(client)
    monkeypatch.setattr(billing, "settings", replace(config, stripe_secret_key=""))
    monkeypatch.setattr(billing, "_stripe", REAL_STRIPE_CLIENT)
    assert client.get("/billing/status", headers=headers).json()["configured"] is False
    assert client.post("/billing/checkout-session", headers=headers).status_code == 503
    assert client.post("/billing/webhook", json=event()).status_code == 503
    gateway.v1.checkout.sessions.create.assert_not_called()


def test_signed_basil_invoice_retrieves_subscription_from_parent(saas):
    client, factory, gateway, config = saas
    data, _ = credentials(client)
    set_tenant(factory, data["tenant_id"], stripe_customer_id="cus_test")
    gateway.v1.subscriptions.retrieve.return_value = subscription(data["tenant_id"])
    invoice = event(kind="invoice.payment_succeeded")
    invoice["data"]["object"] = {"id": "in_basil", "customer": "cus_test", "parent": {
        "type": "subscription_details", "subscription_details": {"subscription": "sub_one"}}}
    assert webhook(client, config, invoice).status_code == 200
    gateway.v1.subscriptions.retrieve.assert_called_once_with("sub_one", {"expand": ["latest_invoice"]})


def test_expired_active_period_blocks_even_without_cancellation_webhook(saas):
    client, factory, _, _ = saas
    data, headers = credentials(client)
    set_tenant(factory, data["tenant_id"], subscription_status="active", current_period_end=datetime(2000, 1, 1))
    assert client.get("/business", headers=headers).status_code == 402
    assert client.get("/billing/status", headers=headers).json()["access_allowed"] is False
    assert client.get("/auth/me", headers=headers).status_code == 200


def test_production_app_binds_gate_to_every_business_router(saas, monkeypatch):
    from main import app

    client, factory, _, _ = saas
    data, headers = credentials(client)
    set_tenant(factory, data["tenant_id"], trial_ends_at=datetime(2000, 1, 1))

    def override():
        with factory() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override)
    monkeypatch.setattr("audit.SessionLocal", factory)
    actual = TestClient(app)
    try:
        for path in ("/users", "/clients", "/professionals", "/services", "/service-categories",
                     "/products", "/appointments", "/loyalty/overview", "/referrals", "/dashboard/kpis",
                     "/reports/clients", "/audit-logs"):
            result = actual.get(path, headers=headers)
            assert result.status_code == 402, (path, result.text)
        assert actual.get("/billing/status", headers=headers).status_code == 200
        assert actual.get("/auth/me", headers=headers).status_code == 200
        assert actual.get("/tenants/export", headers=headers).status_code == 200
    finally:
        actual.close()
