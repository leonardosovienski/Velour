import pytest
from routers.appointments import POINTS_REDEMPTION_RATE, MAX_DISCOUNT_RATIO


def apply_discount(price: float, points: int) -> tuple[float, float]:
    """Replica o cálculo de desconto de _apply_loyalty_completion. Retorna (desconto, preço_final)."""
    discount = points * POINTS_REDEMPTION_RATE
    max_discount = price * MAX_DISCOUNT_RATIO
    discount = min(discount, max_discount)
    final = max(price - discount, 0)
    return discount, final


def test_resgate_minimo_100_pts():
    discount, final = apply_discount(200.0, 100)
    assert discount == pytest.approx(10.0)
    assert final == pytest.approx(190.0)


def test_apenas_multiplos_de_100():
    # 200 pts = R$20 desconto
    discount, final = apply_discount(200.0, 200)
    assert discount == pytest.approx(20.0)
    assert final == pytest.approx(180.0)


def test_teto_50_porcento():
    # 2000 pts = R$200 desconto, mas preço R$150 → teto = R$75
    discount, final = apply_discount(150.0, 2000)
    assert discount == pytest.approx(75.0)
    assert final == pytest.approx(75.0)


def test_exemplo_200_reais_200_pts():
    # R$200, 200 pts → desconto R$20, cobra R$180
    discount, final = apply_discount(200.0, 200)
    assert discount == pytest.approx(20.0)
    assert final == pytest.approx(180.0)


def test_desconto_nao_negativo():
    # Desconto nunca deixa o preço negativo
    _, final = apply_discount(50.0, 10000)
    assert final >= 0


def test_zero_pontos_sem_desconto():
    discount, final = apply_discount(200.0, 0)
    assert discount == pytest.approx(0.0)
    assert final == pytest.approx(200.0)
