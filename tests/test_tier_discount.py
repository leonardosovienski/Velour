import pytest

from models.appointment import AppointmentStatus
from models.client import LoyaltyTier
from routers.appointments import _apply_loyalty_completion, TIER_DISCOUNT_RATES
from tests.conftest import make_client, make_professional, make_category, make_service, make_appointment


def _setup(db, tier, price=100.0, total_spent=0.0, points_reward=0):
    client = make_client(db)
    client.loyalty_tier = tier
    client.total_spent = total_spent
    prof = make_professional(db)
    cat = make_category(db)
    svc = make_service(db, cat.id, price=price, points_reward=points_reward)
    appt = make_appointment(db, client.id, prof.id, svc.id, status="completed")
    appt.price_charged = price
    appt.discount_points_used = 0
    db.flush()
    return db, client, appt


# ── Taxa por tier ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("tier,esperado", [
    (LoyaltyTier.bronze, 100.0),
    (LoyaltyTier.silver, 95.0),
    (LoyaltyTier.gold, 90.0),
    (LoyaltyTier.platinum, 85.0),
])
def test_desconto_por_tier(db, tier, esperado):
    db, client, appt = _setup(db, tier, price=100.0)
    _apply_loyalty_completion(db, appt)
    db.commit()
    db.refresh(appt)
    assert appt.price_charged == pytest.approx(esperado)
    assert appt.tier_discount_amount == pytest.approx(100.0 - esperado)
    assert appt.tier_at_service == tier


def test_taxas_conferem_com_a_regra_de_negocio():
    assert TIER_DISCOUNT_RATES[LoyaltyTier.silver] == 0.05
    assert TIER_DISCOUNT_RATES[LoyaltyTier.gold] == 0.10
    assert TIER_DISCOUNT_RATES[LoyaltyTier.platinum] == 0.15
    assert TIER_DISCOUNT_RATES[LoyaltyTier.bronze] == 0.0


# ── total_spent acumula o valor efetivamente pago ────────────────────────────

def test_total_spent_usa_preco_com_desconto(db):
    db, client, appt = _setup(db, LoyaltyTier.gold, price=200.0)
    _apply_loyalty_completion(db, appt)
    db.commit()
    db.refresh(client)
    # Gold 10% sobre 200 = 180 pago
    assert client.total_spent == pytest.approx(180.0)


# ── Teto combinado tier + pontos = 50% do valor base ─────────────────────────

def test_teto_combinado_tier_mais_pontos(db):
    db, client, appt = _setup(db, LoyaltyTier.platinum, price=100.0)
    client.loyalty_points = 5000
    appt.discount_points_used = 1000   # 1000 pts = R$100 de desconto bruto
    db.flush()

    _apply_loyalty_completion(db, appt)
    db.commit()
    db.refresh(appt)
    db.refresh(client)

    # tier 15% (R$15) + pontos limitado a 35 → desconto total = 50% (R$50)
    assert appt.price_charged == pytest.approx(50.0)
    assert appt.tier_discount_amount == pytest.approx(15.0)
    # pontos debitados integralmente, mesmo com o teto
    assert client.loyalty_points == 5000 - 1000 + int(50.0)


# ── Captura do tier ANTES do recálculo de total_spent ────────────────────────

def test_tier_capturado_antes_do_upgrade(db):
    # Gold quase em Platinum: usa o desconto de Gold neste atendimento,
    # e só DEPOIS sobe para Platinum.
    db, client, appt = _setup(db, LoyaltyTier.gold, price=200.0, total_spent=2900.0)
    _apply_loyalty_completion(db, appt)
    db.commit()
    db.refresh(appt)
    db.refresh(client)

    assert appt.tier_at_service == LoyaltyTier.gold          # usou 10%, não 15%
    assert appt.price_charged == pytest.approx(180.0)
    assert client.total_spent == pytest.approx(3080.0)
    assert client.loyalty_tier == LoyaltyTier.platinum       # upgrade após o atendimento
