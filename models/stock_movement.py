from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from database import Base


class StockMovementType(str, enum.Enum):
    purchase = "purchase"        # entrada por compra/reposição
    consumption = "consumption"  # saída por execução de serviço
    loss = "loss"                # perda/descarte (validade, quebra)
    adjustment = "adjustment"    # ajuste manual de inventário


class StockMovement(Base):
    """
    Ledger append-only de movimentações de estoque.
    Nunca sofre UPDATE/DELETE — cada linha registra uma mudança de saldo.
    `qty` é assinado: positivo = entrada, negativo = saída.
    """
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    type = Column(SAEnum(StockMovementType), nullable=False)
    qty = Column(Float, nullable=False)         # assinado: + entrada, - saída
    qty_before = Column(Float, nullable=False)  # saldo antes da movimentação
    qty_after = Column(Float, nullable=False)   # saldo depois da movimentação
    description = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="movements")
    appointment = relationship("Appointment", back_populates="stock_movements")
