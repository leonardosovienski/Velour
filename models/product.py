from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, Enum as SAEnum
from sqlalchemy.orm import relationship

from database import Base


class ProductUnit(str, enum.Enum):
    """Unidade de medida do insumo."""
    ml = "ml"
    g = "g"
    unit = "unit"  # unidades inteiras (ex.: par de luvas, touca)


class Product(Base):
    """Insumo de estoque consumido na execução dos serviços."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    unit = Column(SAEnum(ProductUnit), nullable=False, default=ProductUnit.ml)
    stock_qty = Column(Float, nullable=False, default=0.0)        # saldo atual
    min_stock = Column(Float, nullable=False, default=0.0)        # gatilho de alerta de reposição
    expiry_date = Column(Date, nullable=True)                     # vencimento (alerta a < 30 dias)
    cost_per_unit = Column(Float, nullable=False, default=0.0)    # custo por unidade de medida
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    recipes = relationship("ServiceRecipe", back_populates="product")
    movements = relationship("StockMovement", back_populates="product")
