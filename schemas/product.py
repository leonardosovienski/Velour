from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field

from models.product import ProductUnit
from models.stock_movement import StockMovementType


# ── Produto / insumo ─────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    unit: ProductUnit = ProductUnit.ml
    stock_qty: float = Field(default=0.0, ge=0)
    min_stock: float = Field(default=0.0, ge=0)
    expiry_date: Optional[date] = None
    cost_per_unit: float = Field(default=0.0, ge=0)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    unit: Optional[ProductUnit] = None
    min_stock: Optional[float] = Field(None, ge=0)
    expiry_date: Optional[date] = None
    cost_per_unit: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    # stock_qty NÃO é editável aqui: saldo só muda via movimentações (ledger)


class ProductResponse(BaseModel):
    id: int
    name: str
    unit: ProductUnit
    stock_qty: float
    min_stock: float
    expiry_date: Optional[date]
    cost_per_unit: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Entrada manual de estoque ────────────────────────────────────────────────

class StockEntry(BaseModel):
    """Reposição/ajuste manual de saldo. Gera uma StockMovement."""
    qty: float = Field(gt=0, description="Quantidade a adicionar (sempre positiva)")
    type: StockMovementType = StockMovementType.purchase
    description: Optional[str] = None


class StockMovementResponse(BaseModel):
    id: int
    product_id: int
    appointment_id: Optional[int]
    type: StockMovementType
    qty: float
    qty_before: float
    qty_after: float
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Ficha técnica (receita do serviço) ───────────────────────────────────────

class RecipeItem(BaseModel):
    product_id: int
    qty_consumed: float = Field(gt=0)


class ServiceRecipeResponse(BaseModel):
    id: int
    service_id: int
    product_id: int
    product_name: str
    unit: ProductUnit
    qty_consumed: float

    model_config = {"from_attributes": True}


# ── Override de dosagem no checkout ──────────────────────────────────────────

class RecipeOverride(BaseModel):
    """Ajuste da quantidade real consumida no fechamento (ex.: coloração varia)."""
    product_id: int
    actual_qty: float = Field(ge=0)
