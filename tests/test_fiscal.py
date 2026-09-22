from dataclasses import replace
from decimal import Decimal

import pytest

from database import system_scope, tenant_scope
from models import Appointment, AppointmentStatus, FiscalDocument, Tenant, User, UserRole
from routers import fiscal
from tests.test_tenancy import headers, isolated_accounts, tenant_api  # noqa: F401


PARTY = {"legal_name": "Pessoa de demonstração", "tax_id": "52998224725", "email": "demo@example.com",
         "street": "Rua de Teste", "number": "10", "district": "Centro", "postal_code": "83702000",
         "city": "Araucária", "municipality_code": "4101804", "state": "PR"}
PROFILE = {**PARTY, "legal_name": "Salão de demonstração", "tax_id": "11222333000181",
           "municipal_registration": "1234", "tax_regime": "simples", "service_code": "060101", "iss_rate": "2.50"}


@pytest.fixture
def fiscal_api(tenant_api, monkeypatch):
    api, factory, accounts = tenant_api
    monkeypatch.setattr(fiscal, "settings", replace(fiscal.settings, fiscal_mode="demo",
                                                  fiscal_demo_platform_user_id=accounts[0]["user"], environment="test"))
    for account in accounts:
        with factory() as db:
            tenant_scope(db, account["tenant"])
            appointment = db.get(Appointment, account["appointment"])
            appointment.status = AppointmentStatus.completed
            appointment.price_charged = Decimal("101.10")
            db.commit()
        assert api.put("/fiscal/profile", json=PROFILE, headers=headers(account)).status_code == 200
    return api, factory, accounts


def draft(account, **extra):
    return {"appointment_id": account["appointment"], "competence": "2026-09-15",
            "description": "Corte de demonstração", "service_code": "060101", "iss_rate": "2.50", "recipient": PARTY, **extra}


def create(api, account, **extra):
    result = api.post("/fiscal/documents", json=draft(account, **extra), headers=headers(account))
    assert result.status_code == 201, result.text
    return result.json()


def test_fiscal_lifecycle_amount_snapshot_idempotency_and_html(fiscal_api):
    api, factory, (a, b) = fiscal_api
    doc = create(api, a, description="Serviço <script>alert(1)</script>")
    path = f"/fiscal/documents/{doc['id']}"
    assert doc["amount"] == 101.10
    assert doc["iss_amount"] == 2.53  # exact Decimal half-up
    assert doc["environment"] == "demo" and doc["status"] == "draft"
    assert api.post("/fiscal/documents", json=draft(a), headers=headers(a)).status_code == 409
    assert api.post("/fiscal/documents", json=draft(a, amount=1), headers=headers(a)).status_code == 422
    assert api.put("/fiscal/profile", json={**PROFILE, "legal_name": "Novo nome"}, headers=headers(a)).status_code == 200
    assert api.get(path, headers=headers(a)).json()["issuer"]["legal_name"] == PROFILE["legal_name"]
    for _ in range(2):
        response = api.post(path + "/simulate", headers=headers(a))
        assert response.status_code == 200, response.text
        assert response.json()["number"].startswith("DEMO-")
    response = api.get(path + "/print", headers=headers(a))
    assert "SEM VALIDADE FISCAL" in response.text
    assert "<script>" not in response.text and "&lt;script&gt;" in response.text
    assert response.headers["cache-control"] == "no-store"
    for _ in range(2):
        response = api.post(path + "/cancel", json={"reason": "Cancelamento solicitado para demonstração"}, headers=headers(a))
        assert response.status_code == 200
    assert api.post(path + "/simulate", headers=headers(a)).status_code == 409
    assert [e["action"] for e in api.get(path + "/events", headers=headers(a)).json()] == ["created", "simulate", "cancel"]
    assert api.get("/fiscal/appointments", headers=headers(a)).json() == []
    export = api.get("/tenants/export", headers=headers(a)).json()["data"]
    assert export["fiscal_documents"][0]["id"] == doc["id"]


def test_fiscal_tenant_isolation_and_server_authorization(fiscal_api):
    api, factory, (a, b) = fiscal_api
    doc = create(api, b)
    for suffix in ("", "/events", "/print"):
        assert api.get(f"/fiscal/documents/{doc['id']}" + suffix, headers=headers(a)).status_code == 404
    for suffix, payload in (("/simulate", {}), ("/cancel", {"reason": "Tentativa de outro salão"})):
        assert api.post(f"/fiscal/documents/{doc['id']}" + suffix, json=payload, headers=headers(a)).status_code == 404
    assert api.get("/fiscal/documents", headers=headers(a)).json() == []
    assert api.post("/fiscal/documents", json=draft(b), headers=headers(a)).status_code == 404
    for role in (UserRole.manager, UserRole.professional):
        with factory() as db:
            tenant_scope(db, a["tenant"])
            db.get(User, a["user"]).role = role
            db.commit()
        assert api.get("/fiscal/config", headers=headers(a)).status_code == 403
        assert api.put("/fiscal/profile", json=PROFILE, headers=headers(a)).status_code == 403
        assert api.get("/fiscal-platform/tenants", headers=headers(a)).status_code == 403


def test_platform_demo_separation_and_received_documents(fiscal_api, monkeypatch):
    api, factory, (a, b) = fiscal_api
    assert api.get("/fiscal/config", headers=headers(a)).json()["can_manage_platform"] is True
    assert api.get("/fiscal-platform/tenants", headers=headers(b)).status_code == 403
    assert api.put("/fiscal-platform/profile", json=PROFILE, headers=headers(a)).status_code == 200
    body = {k: v for k, v in draft(a).items() if k != "appointment_id"}
    body.update(tenant_id=b["tenant"], subscription_reference="demo-2026-09", amount="199.90")
    response = api.post("/fiscal-platform/documents", json=body, headers=headers(a))
    assert response.status_code == 201, response.text
    doc = response.json()
    path = f"/fiscal-platform/documents/{doc['id']}"
    assert api.post(path + "/simulate", headers=headers(a)).status_code == 200
    received = api.get("/fiscal/documents?kind=platform", headers=headers(b)).json()
    assert len(received) == 1 and received[0]["amount"] == 199.90
    assert api.get("/fiscal/documents?kind=platform", headers=headers(a)).json() == []
    assert api.post(f"/fiscal/documents/{doc['id']}/cancel", json={"reason": "Tomador não pode cancelar"}, headers=headers(b)).status_code == 403
    assert api.post(f"/fiscal/documents/{doc['id']}/simulate", headers=headers(b)).status_code == 403
    assert api.post("/fiscal-platform/documents", json=body, headers=headers(a)).status_code == 409
    assert api.post(path + "/cancel", json={"reason": "Demonstração de cancelamento"}, headers=headers(a)).status_code == 200
    monkeypatch.setattr(fiscal, "settings", replace(fiscal.settings, environment="production"))
    assert api.get("/fiscal-platform/documents", headers=headers(a)).status_code == 403


@pytest.mark.parametrize("field,value", [("tax_id", "11111111111"), ("tax_id", "52998224726"),
                                         ("tax_id", "11222333000182"), ("state", "XX"), ("postal_code", "123")])
def test_invalid_fiscal_party_is_rejected(fiscal_api, field, value):
    api, _, (a, _) = fiscal_api
    assert api.post("/fiscal/documents", json=draft(a, recipient={**PARTY, field: value}), headers=headers(a)).status_code == 422


def test_disabled_mode_and_expired_account_preserve_read_access(fiscal_api, monkeypatch):
    api, factory, (a, _) = fiscal_api
    doc = create(api, a)
    with factory() as db, system_scope(db):
        db.get(Tenant, a["tenant"]).subscription_status = "cancelled"
        db.commit()
    assert api.get("/fiscal/documents", headers=headers(a)).status_code == 200
    assert api.get(f"/fiscal/documents/{doc['id']}/print", headers=headers(a)).status_code == 200
    assert api.post(f"/fiscal/documents/{doc['id']}/simulate", headers=headers(a)).status_code == 402
    monkeypatch.setattr(fiscal, "settings", replace(fiscal.settings, fiscal_mode="disabled"))
    assert api.put("/fiscal/profile", json=PROFILE, headers=headers(a)).status_code == 503
    assert api.get(f"/fiscal/documents/{doc['id']}", headers=headers(a)).status_code == 200


def test_incomplete_appointment_and_zero_value_cannot_generate_document(fiscal_api):
    api, factory, (a, _) = fiscal_api
    for status, amount in ((AppointmentStatus.scheduled, Decimal("50")), (AppointmentStatus.completed, Decimal("0"))):
        with factory() as db:
            tenant_scope(db, a["tenant"])
            appt = db.get(Appointment, a["appointment"])
            appt.status, appt.price_charged = status, amount
            db.commit()
        assert api.post("/fiscal/documents", json=draft(a), headers=headers(a)).status_code == 409
