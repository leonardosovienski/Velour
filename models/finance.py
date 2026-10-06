from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, CheckConstraint, UniqueConstraint
from database import Base, TenantScoped
from models.fiscal import utcnow


class Expense(TenantScoped, Base):
    __tablename__ = 'expenses'
    __table_args__ = (CheckConstraint('amount > 0', name='ck_expenses_positive_amount'),)
    id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    category = Column(String(30), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    paid_on = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class CostBudget(TenantScoped, Base):
    """Orçamento mensal por linha de custo (AAAA-MM), comparado ao realizado na gestão de custos."""
    __tablename__ = 'cost_budgets'
    __table_args__ = (
        CheckConstraint('amount >= 0', name='ck_cost_budgets_non_negative_amount'),
        UniqueConstraint('tenant_id', 'month', 'category', name='uq_cost_budgets_tenant_month_category'),
    )
    id = Column(Integer, primary_key=True)
    month = Column(String(7), nullable=False)
    category = Column(String(30), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
