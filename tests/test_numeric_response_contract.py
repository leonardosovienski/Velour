"""Real HTTP responses must match the SPA's numeric money/rate fields."""
from decimal import Decimal

import pytest

from database import tenant_scope
from models import Product, Service
from schemas.appointment import AppointmentComplete, AppointmentResponse
from schemas.client import ClientResponse
from schemas.product import ProductCreate, ProductResponse
from schemas.professional import ProfessionalResponse
from schemas.service import ServiceCreate, ServiceResponse
from tests.test_tenancy import headers, isolated_accounts, tenant_api  # noqa: F401 — pytest fixtures


def test_real_api_money_and_rates_are_json_numbers(tenant_api):
    api, factory, (account, other) = tenant_api
    with factory() as db:
        tenant_scope(db, account["tenant"])
        db.add(Product(name="Precisão de custo", unit="ml", cost_per_unit=Decimal("0.1234")))
        db.commit()

    auth = headers(account)
    endpoints = {
        "/services": ["price"],
        "/products": ["cost_per_unit"],
        "/professionals": ["commission_rate", "monthly_goal"],
        "/clients": ["total_spent"],
        "/appointments": ["price_charged", "tier_discount_amount"],
    }
    for endpoint, fields in endpoints.items():
        response = api.get(endpoint, headers=auth)
        assert response.status_code == 200, response.text
        assert response.json()
        for row in response.json():
            for field in fields:
                assert type(row[field]) in (float, int), (endpoint, field, row[field])
    assert api.get("/products", headers=auth).json()[0]["cost_per_unit"] == 0.1234
    appointment = api.get(f"/appointments/{account['appointment']}", headers=auth).json()
    assert type(appointment["service"]["price"]) in (float, int)
    assert type(appointment["professional"]["commission_rate"]) in (float, int)
    assert type(appointment["client"]["total_spent"]) in (float, int)
    assert appointment["amount_paid"] is None
    briefing = api.get(f"/clients/{account['client']}/briefing", headers=auth).json()
    assert type(briefing["total_spent"]) in (float, int)
    assert type(briefing["spent_to_next_tier"]) in (float, int)


def test_serialization_preserves_decimal_in_python_and_input_validation(tenant_api):
    api, factory, (account, other) = tenant_api
    with factory() as db:
        tenant_scope(db, account["tenant"])
        service = db.get(Service, account["service"])
        service.price = Decimal("100.10")
        response = ServiceResponse.model_validate(service)
        assert response.price == Decimal("100.10")
        assert isinstance(response.model_dump()["price"], Decimal)
        assert response.model_dump(mode="json")["price"] == 100.1
    inputs = [ServiceCreate(category_id=1, name="Serviço", duration_minutes=60, price="100.10"),
              ProductCreate(name="Produto", cost_per_unit="0.1234"),
              AppointmentComplete(price_charged="100.10", amount_paid="100.10")]
    assert isinstance(inputs[0].model_dump()["price"], Decimal)
    assert isinstance(inputs[1].model_dump()["cost_per_unit"], Decimal)
    assert isinstance(inputs[2].model_dump()["amount_paid"], Decimal)


@pytest.mark.parametrize("schema,field", [(ServiceResponse, "price"), (ProductResponse, "cost_per_unit"),
    (ProfessionalResponse, "commission_rate"), (ProfessionalResponse, "monthly_goal"),
    (ClientResponse, "total_spent"), (AppointmentResponse, "tier_discount_amount")])
def test_response_json_schema_advertises_numeric_fields(schema, field):
    assert schema.model_json_schema(mode="serialization")["properties"][field]["type"] == "number"
