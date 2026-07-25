from datetime import date, timedelta

import pytest

from routers.dashboard import alerts
from models.product import Product, ProductUnit


def _product(db, name, stock_qty, min_stock, expiry_date=None):
    p = Product(name=name, unit=ProductUnit.ml, stock_qty=stock_qty,
                min_stock=min_stock, expiry_date=expiry_date)
    db.add(p)
    db.flush()
    return p


def test_alerta_de_estoque_baixo(db):
    _product(db, "Abaixo do minimo", stock_qty=50, min_stock=100)
    _product(db, "No limite", stock_qty=100, min_stock=100)   # <= min também alerta
    _product(db, "Saudavel", stock_qty=500, min_stock=100)

    res = alerts(db=db, _=None)
    nomes = {p["name"] for p in res["low_stock"]}

    assert "Abaixo do minimo" in nomes
    assert "No limite" in nomes
    assert "Saudavel" not in nomes


def test_alerta_de_validade_proxima(db):
    _product(db, "Vence em 10 dias", stock_qty=500, min_stock=100,
             expiry_date=date.today() + timedelta(days=10))
    _product(db, "Vence em 90 dias", stock_qty=500, min_stock=100,
             expiry_date=date.today() + timedelta(days=90))
    _product(db, "Sem validade", stock_qty=500, min_stock=100)

    res = alerts(db=db, _=None)
    nomes = {p["name"] for p in res["expiring_soon"]}

    assert "Vence em 10 dias" in nomes
    assert "Vence em 90 dias" not in nomes
    assert "Sem validade" not in nomes


def test_produto_vencido_tambem_alerta(db):
    _product(db, "Vencido", stock_qty=500, min_stock=100,
             expiry_date=date.today() - timedelta(days=5))

    res = alerts(db=db, _=None)
    vencido = next(p for p in res["expiring_soon"] if p["name"] == "Vencido")
    assert vencido["days_to_expiry"] == -5
