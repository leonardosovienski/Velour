from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, joinedload

from auth import require_manager
from database import get_db
from domain_locks import serialized_mutation
from models import Appointment, AppointmentStatus, Expense, FiscalDocument
from models.appointment import PaymentMethod
from schemas.numbers import JsonDecimal

router = APIRouter(prefix='/finance', tags=['finance'])


class ExpenseInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    description: str = Field(min_length=3, max_length=200)
    category: Literal['rent', 'supplies', 'utilities', 'people', 'other']
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    due_date: date
    paid_on: date | None = None


class ExpenseResponse(ExpenseInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: JsonDecimal


class ExpensePayment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    paid_on: date


class ReceiptPayment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    payment_method: PaymentMethod


def received(appointment):
    return (appointment.amount_paid or Decimal('0')) if appointment.paid else Decimal('0')


@router.get('/overview')
def overview(month: str = Query(pattern=r'^\d{4}-(0[1-9]|1[0-2])$'),
             user=Depends(require_manager), db: Session = Depends(get_db)):
    try:
        start = date.fromisoformat(month + '-01')
        end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    except ValueError:
        raise HTTPException(422, 'Mês inválido')
    rows = db.query(Appointment).options(joinedload(Appointment.client), joinedload(Appointment.service)).filter(Appointment.status == AppointmentStatus.completed,
        Appointment.scheduled_at >= datetime.combine(start, datetime.min.time()),
        Appointment.scheduled_at < datetime.combine(end, datetime.min.time())).order_by(Appointment.scheduled_at.desc()).all()
    expenses = db.query(Expense).filter(Expense.due_date >= start, Expense.due_date < end).order_by(Expense.due_date, Expense.id).all()
    docs = {d.appointment_id: d for d in db.query(FiscalDocument).filter(
        FiscalDocument.issuer_kind == 'salon', FiscalDocument.appointment_id.in_([a.id for a in rows])).all()}
    total_received = sum((received(a) for a in rows), Decimal('0'))
    paid_expenses = sum((e.amount for e in expenses if e.paid_on), Decimal('0'))
    # Grouping is by service/due month, not payment date. Do not call this bank balance.
    return {'month': month, 'received': total_received,
        'receivable': sum((max(Decimal('0'), (a.price_charged or Decimal('0')) - received(a)) for a in rows), Decimal('0')),
        'expenses_paid': paid_expenses,
        'expenses_pending': sum((e.amount for e in expenses if not e.paid_on), Decimal('0')),
        'balance': total_received - paid_expenses,
        'receipts': [{'id': a.id, 'client': a.client.name, 'service': a.service.name,
            'date': a.scheduled_at.date(), 'amount': a.price_charged or Decimal('0'), 'received': received(a),
            'remaining': max(Decimal('0'), (a.price_charged or Decimal('0')) - received(a)),
            'payment_method': a.payment_method if a.paid else None,
            'document_id': docs[a.id].id if a.id in docs else None,
            'document_status': docs[a.id].status if a.id in docs else None} for a in rows],
        'expenses': [ExpenseResponse.model_validate(e).model_dump(mode='json') for e in expenses]}


@router.post('/expenses', response_model=ExpenseResponse, status_code=201)
@serialized_mutation
def add_expense(body: ExpenseInput, user=Depends(require_manager), db: Session = Depends(get_db)):
    if body.paid_on and body.paid_on > date.today():
        raise HTTPException(422, 'A data de pagamento não pode estar no futuro')
    expense = Expense(tenant_id=user.tenant_id, **body.model_dump())
    db.add(expense)
    db.commit()
    return expense


@router.post('/expenses/{expense_id}/pay', response_model=ExpenseResponse)
@serialized_mutation
def pay_expense(expense_id: int, body: ExpensePayment, user=Depends(require_manager), db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(404, 'Despesa não encontrada')
    if body.paid_on > date.today():
        raise HTTPException(422, 'A data de pagamento não pode estar no futuro')
    if not expense.paid_on:
        expense.paid_on = body.paid_on
        db.commit()
    return expense


@router.post('/receipts/{appointment_id}/settle')
@serialized_mutation
def settle_receipt(appointment_id: int, body: ReceiptPayment, user=Depends(require_manager), db: Session = Depends(get_db)):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, 'Atendimento não encontrado')
    if appointment.status != AppointmentStatus.completed or not appointment.price_charged or appointment.price_charged <= 0:
        raise HTTPException(409, 'Somente atendimentos concluídos com valor positivo podem ser recebidos')
    if received(appointment) < appointment.price_charged:
        appointment.paid = True
        appointment.amount_paid = appointment.price_charged
        appointment.payment_method = body.payment_method
        db.commit()
    return {'id': appointment.id, 'received': received(appointment)}
