from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, CheckConstraint
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
