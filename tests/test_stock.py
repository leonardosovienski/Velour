import pytest

from fastapi import HTTPException

from models.appointment import AppointmentStatus
from models.product import Product, ProductUnit
from models.service_recipe import ServiceRecipe
from models.stock_movement import StockMovement, StockMovementType
from routers.appointments import _apply_stock_deduction
from schemas.appointment import RecipeOverride
from tests.conftest import make_client, make_professional, make_category, make_service, make_appointment


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_product(db, name="Insumo", unit=ProductUnit.ml, stock_qty=1000.0, min_stock=100.0):
    p = Product(name=name, unit=unit, stock_qty=stock_qty, min_stock=min_stock)
    db.add(p)
    db.flush()
    return p


def make_recipe(db, service_id, product_id, qty_consumed):
    r = ServiceRecipe(service_id=service_id, product_id=product_id, qty_consumed=qty_consumed)
    db.add(r)
    db.flush()
    return r


@pytest.fixture
def stock_setup(db):
    client = make_client(db)
    prof = make_professional(db)
    cat = make_category(db)
    svc = make_service(db, cat.id, price=100.0, points_reward=0)
    appt = make_appointment(db, client.id, prof.id, svc.id, status="completed")
    return db, svc, appt


# ── Baixa padrão pela ficha técnica ──────────────────────────────────────────

def test_baixa_padrao_deduz_da_receita(stock_setup):
    db, svc, appt = stock_setup
    prod = make_product(db, stock_qty=1000.0)
    make_recipe(db, svc.id, prod.id, qty_consumed=60.0)

    _apply_stock_deduction(db, appt, None)
    db.commit()
    db.refresh(prod)

    assert prod.stock_qty == pytest.approx(940.0)


def test_baixa_registra_movimento_no_ledger(stock_setup):
    db, svc, appt = stock_setup
    prod = make_product(db, stock_qty=1000.0)
    make_recipe(db, svc.id, prod.id, qty_consumed=60.0)

    _apply_stock_deduction(db, appt, None)
    db.commit()

    mov = db.query(StockMovement).filter(StockMovement.product_id == prod.id).one()
    assert mov.type == StockMovementType.consumption
    assert mov.qty == pytest.approx(-60.0)
    assert mov.qty_before == pytest.approx(1000.0)
    assert mov.qty_after == pytest.approx(940.0)
    assert mov.appointment_id == appt.id


# ── Override de dosagem (coloração varia) ────────────────────────────────────

def test_override_substitui_dosagem(stock_setup):
    db, svc, appt = stock_setup
    prod = make_product(db, stock_qty=1000.0)
    make_recipe(db, svc.id, prod.id, qty_consumed=60.0)

    # Profissional usou 80ml em vez dos 60ml padrão
    _apply_stock_deduction(db, appt, [RecipeOverride(product_id=prod.id, actual_qty=80.0)])
    db.commit()
    db.refresh(prod)

    assert prod.stock_qty == pytest.approx(920.0)


def test_override_adiciona_insumo_fora_da_receita(stock_setup):
    db, svc, appt = stock_setup
    na_receita = make_product(db, name="Na receita", stock_qty=500.0)
    make_recipe(db, svc.id, na_receita.id, qty_consumed=30.0)
    extra = make_product(db, name="Extra", stock_qty=500.0)

    _apply_stock_deduction(db, appt, [RecipeOverride(product_id=extra.id, actual_qty=25.0)])
    db.commit()
    db.refresh(na_receita)
    db.refresh(extra)

    assert na_receita.stock_qty == pytest.approx(470.0)  # receita aplicada
    assert extra.stock_qty == pytest.approx(475.0)       # insumo extra deduzido


def test_override_zero_ignora_insumo(stock_setup):
    db, svc, appt = stock_setup
    prod = make_product(db, stock_qty=1000.0)
    make_recipe(db, svc.id, prod.id, qty_consumed=60.0)

    _apply_stock_deduction(db, appt, [RecipeOverride(product_id=prod.id, actual_qty=0.0)])
    db.commit()
    db.refresh(prod)

    assert prod.stock_qty == pytest.approx(1000.0)  # nada consumido
    assert db.query(StockMovement).filter(StockMovement.product_id == prod.id).count() == 0


# ── Operação não trava: saldo pode ficar negativo ────────────────────────────

def test_estoque_negativo_nao_trava(stock_setup):
    db, svc, appt = stock_setup
    prod = make_product(db, stock_qty=50.0, min_stock=20.0)
    make_recipe(db, svc.id, prod.id, qty_consumed=80.0)  # consome mais do que tem

    _apply_stock_deduction(db, appt, None)
    db.commit()
    db.refresh(prod)

    assert prod.stock_qty == pytest.approx(-30.0)  # ficou negativo, mas concluiu
    mov = db.query(StockMovement).filter(StockMovement.product_id == prod.id).one()
    assert mov.qty_after == pytest.approx(-30.0)


# ── Casos de borda ───────────────────────────────────────────────────────────

def test_servico_sem_receita_nao_movimenta(stock_setup):
    db, svc, appt = stock_setup
    make_product(db, stock_qty=1000.0)  # produto existe mas não está em receita

    _apply_stock_deduction(db, appt, None)
    db.commit()

    assert db.query(StockMovement).count() == 0


def test_override_produto_inexistente_levanta_422(stock_setup):
    db, svc, appt = stock_setup

    with pytest.raises(HTTPException) as exc:
        _apply_stock_deduction(db, appt, [RecipeOverride(product_id=99999, actual_qty=10.0)])
    assert exc.value.status_code == 422
