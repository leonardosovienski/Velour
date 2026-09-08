import pytest

from database import tenant_scope
from models import Service
from tests.test_tenancy import headers, isolated_accounts, tenant_api  # noqa: F401 — pytest fixtures


@pytest.mark.parametrize("active", [True, False])
def test_category_with_services_is_a_conflict_until_services_are_moved(tenant_api, active):
    api, factory, (account, other) = tenant_api
    auth = headers(account)
    with factory() as db:
        tenant_scope(db, account["tenant"])
        db.get(Service, account["service"]).is_active = active
        db.commit()
    category_url = f"/service-categories/{account['category']}"
    assert api.delete(category_url, headers=auth).status_code == 409
    assert api.get(f"/services/{account['service']}", headers=auth).json()["category_id"] == account["category"]
    assert api.delete(f"/service-categories/{other['category']}", headers=auth).status_code == 404
    assert api.patch(f"/services/{account['service']}", json={"category_id": other["category"]}, headers=auth).status_code == 404
    created = api.post("/service-categories", json={"name": "Categoria de destino"}, headers=auth)
    assert created.status_code == 201
    moved = api.patch(f"/services/{account['service']}", json={"category_id": created.json()["id"]}, headers=auth)
    assert moved.status_code == 200
    assert api.delete(category_url, headers=auth).status_code == 204
    assert api.delete(category_url, headers=auth).status_code == 404


@pytest.mark.parametrize("timestamp", ["2030-02-05T10:30:00Z", "2030-02-05T10:30:00-03:00", "2030-02-05T10:30:00+02:00"])
def test_schedule_rejects_timezone_offsets_in_body_and_filters(tenant_api, timestamp):
    api, factory, (account, other) = tenant_api
    auth = headers(account)
    response = api.post("/appointments", headers=auth, json={
        "client_id": account["client"], "professional_id": account["professional"],
        "service_id": account["service"], "scheduled_at": timestamp,
    })
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "timezone_naive"
    for field in ("date_from", "date_to"):
        assert api.get("/appointments", headers=auth, params={field: timestamp}).status_code == 422


def test_schedule_preserves_salon_wall_clock_and_computes_end_across_midnight(tenant_api):
    api, factory, (account, other) = tenant_api
    auth = headers(account)
    response = api.post("/appointments", headers=auth, json={
        "client_id": account["client"], "professional_id": account["professional"],
        "service_id": account["service"], "scheduled_at": "2030-02-05T23:30",
    })
    assert response.status_code == 201, response.text
    assert response.json()["scheduled_at"] == "2030-02-05T23:30:00"
    assert response.json()["ends_at"] == "2030-02-06T00:30:00"
    listed = api.get("/appointments", headers=auth, params={"date_from": "2030-02-05", "date_to": "2030-02-06T00:00"})
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()] == [response.json()["id"]]
