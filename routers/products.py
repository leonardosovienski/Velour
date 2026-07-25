from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from models.product import Product
from models.service import Service
from models.service_recipe import ServiceRecipe
from models.stock_movement import StockMovement, StockMovementType
from schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    StockEntry, StockMovementResponse,
    RecipeItem, ServiceRecipeResponse,
)

router = APIRouter(tags=["products"])


# ── Produtos / insumos ───────────────────────────────────────────────────────

prod_router = APIRouter(prefix="/products")


@prod_router.get("", response_model=List[ProductResponse])
def list_products(
    is_active: bool = True,
    low_stock: bool = False,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(Product).filter(Product.is_active == is_active)
    if low_stock:
        q = q.filter(Product.stock_qty <= Product.min_stock)
    return q.order_by(Product.name).all()


@prod_router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Insumo não encontrado")
    return product


@prod_router.post("", response_model=ProductResponse, status_code=201)
def create_product(body: ProductCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    product = Product(**body.model_dump())
    db.add(product)
    db.flush()  # garante product.id para o ledger

    # Saldo inicial vira uma entrada no ledger (mantém o histórico íntegro)
    if product.stock_qty > 0:
        db.add(StockMovement(
            product_id=product.id,
            type=StockMovementType.purchase,
            qty=product.stock_qty,
            qty_before=0.0,
            qty_after=product.stock_qty,
            description="Saldo inicial",
        ))

    db.commit()
    db.refresh(product)
    return product


@prod_router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, body: ProductUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Insumo não encontrado")
    # stock_qty propositalmente fora do ProductUpdate: saldo só muda via /stock
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@prod_router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Insumo não encontrado")
    product.is_active = False
    db.commit()


@prod_router.post("/{product_id}/stock", response_model=ProductResponse)
def move_stock(product_id: int, body: StockEntry, db: Session = Depends(get_db), _=Depends(require_admin)):
    """
    Movimentação manual de estoque (entrada por compra, perda ou ajuste).
    `qty` é sempre positiva; o sinal aplicado ao saldo depende do `type`:
      purchase/adjustment → soma · loss → subtrai.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Insumo não encontrado")

    delta = -body.qty if body.type == StockMovementType.loss else body.qty
    qty_before = product.stock_qty
    qty_after = qty_before + delta
    product.stock_qty = qty_after

    db.add(StockMovement(
        product_id=product.id,
        type=body.type,
        qty=delta,
        qty_before=qty_before,
        qty_after=qty_after,
        description=body.description or f"Movimentação manual ({body.type.value})",
    ))
    db.commit()
    db.refresh(product)
    return product


@prod_router.get("/{product_id}/movements", response_model=List[StockMovementResponse])
def list_movements(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(status_code=404, detail="Insumo não encontrado")
    return (
        db.query(StockMovement)
        .filter(StockMovement.product_id == product_id)
        .order_by(StockMovement.created_at.desc(), StockMovement.id.desc())
        .all()
    )


# ── Ficha técnica (receita do serviço) ───────────────────────────────────────

recipe_router = APIRouter(prefix="/services")


@recipe_router.get("/{service_id}/recipe", response_model=List[ServiceRecipeResponse])
def get_recipe(service_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if not db.query(Service).filter(Service.id == service_id).first():
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    rows = (
        db.query(ServiceRecipe)
        .filter(ServiceRecipe.service_id == service_id)
        .all()
    )
    return [
        ServiceRecipeResponse(
            id=r.id,
            service_id=r.service_id,
            product_id=r.product_id,
            product_name=r.product.name,
            unit=r.product.unit,
            qty_consumed=r.qty_consumed,
        )
        for r in rows
    ]


@recipe_router.put("/{service_id}/recipe", response_model=List[ServiceRecipeResponse])
def set_recipe(
    service_id: int,
    items: List[RecipeItem],
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Substitui integralmente a ficha técnica do serviço."""
    if not db.query(Service).filter(Service.id == service_id).first():
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    # Valida insumos e rejeita duplicidade antes de mutar
    seen = set()
    for item in items:
        if item.product_id in seen:
            raise HTTPException(status_code=422, detail=f"Insumo {item.product_id} duplicado na receita")
        seen.add(item.product_id)
        if not db.query(Product).filter(Product.id == item.product_id).first():
            raise HTTPException(status_code=404, detail=f"Insumo {item.product_id} não encontrado")

    db.query(ServiceRecipe).filter(ServiceRecipe.service_id == service_id).delete()
    for item in items:
        db.add(ServiceRecipe(
            service_id=service_id,
            product_id=item.product_id,
            qty_consumed=item.qty_consumed,
        ))
    db.commit()

    return get_recipe(service_id, db)


router.include_router(prod_router)
router.include_router(recipe_router)
