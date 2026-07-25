from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class ServiceRecipe(Base):
    """
    Ficha técnica: quanto de cada insumo um serviço consome por execução.
    Objeto de associação N:N entre Service e Product (carrega qty_consumed).
    """
    __tablename__ = "service_recipes"
    __table_args__ = (
        UniqueConstraint("service_id", "product_id", name="uq_service_product"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    qty_consumed = Column(Float, nullable=False)  # quantidade-padrão na unidade do produto

    service = relationship("Service", back_populates="recipes")
    product = relationship("Product", back_populates="recipes")
