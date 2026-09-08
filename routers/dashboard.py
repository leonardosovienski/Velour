from datetime import datetime, timedelta, date
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from models.user import User
from database import get_db
from models.appointment import Appointment, AppointmentStatus
from models.client import Client
from models.loyalty import LoyaltyTransaction
from models.product import Product

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _scope_appointments(query, current_user: User | None):
    if current_user is not None and current_user.role == "professional":
        if current_user.professional_id is None:
            return query.filter(False)
        return query.filter(Appointment.professional_id == current_user.professional_id)
    return query


@router.get("/today")
def today_summary(db: Session = Depends(get_db), _=Depends(get_current_user)):
    hoje = datetime.now().date()
    inicio = datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0)
    fim = datetime(hoje.year, hoje.month, hoje.day, 23, 59, 59)

    appts_hoje = (
        _scope_appointments(db.query(Appointment), _)
        .filter(Appointment.scheduled_at >= inicio, Appointment.scheduled_at <= fim)
        .order_by(Appointment.scheduled_at)
        .all()
    )

    status_breakdown: dict = {}
    for a in appts_hoje:
        key = a.status.value
        status_breakdown[key] = status_breakdown.get(key, 0) + 1

    receita_hoje = sum(
        (a.price_charged or a.service.price)
        for a in appts_hoje if a.status == AppointmentStatus.completed
    )

    appts_detail = [
        {
            "id": a.id,
            "scheduled_at": a.scheduled_at,
            "ends_at": a.ends_at,
            "status": a.status,
            "client": {"id": a.client.id, "name": a.client.name, "code": a.client.code, "tier": a.client.loyalty_tier},
            "professional": {"id": a.professional.id, "name": a.professional.name},
            "service": {"id": a.service.id, "name": a.service.name, "duration_minutes": a.service.duration_minutes},
            "occasion": a.occasion,
        }
        for a in appts_hoje
    ]

    return {
        "date": hoje.isoformat(),
        "total_appointments": len(appts_hoje),
        "status_breakdown": status_breakdown,
        "revenue_today": round(receita_hoje, 2),
        "appointments": appts_detail,
    }


@router.get("/kpis")
def kpis(period: str = Query("month", pattern="^(day|week|month)$"), db: Session = Depends(get_db), _=Depends(get_current_user)):
    hoje = datetime.now()
    if period == "day":
        inicio = datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0)
    elif period == "week":
        inicio = hoje - timedelta(days=hoje.weekday())
        inicio = datetime(inicio.year, inicio.month, inicio.day, 0, 0, 0)
    else:
        inicio = datetime(hoje.year, hoje.month, 1)

    appts = (
        _scope_appointments(db.query(Appointment), _)
        .filter(Appointment.scheduled_at >= inicio, Appointment.status == AppointmentStatus.completed)
        .all()
    )

    receita = sum(a.price_charged or a.service.price for a in appts)

    clients_query = db.query(Client).filter(Client.is_active == True)
    if _ is not None and _.role == "professional":
        clients_query = clients_query.join(Appointment, Appointment.client_id == Client.id).filter(
            Appointment.professional_id == current_user.professional_id
        ).distinct()
    total_clientes_ativos = clients_query.count()

    pts_emitidos = 0 if _ is not None and _.role == "professional" else (
        db.query(func.sum(LoyaltyTransaction.points))
        .filter(LoyaltyTransaction.created_at >= inicio, LoyaltyTransaction.points > 0)
        .scalar() or 0
    )

    return {
        "period": period,
        "since": inicio.isoformat(),
        "completed_appointments": len(appts),
        "revenue": round(receita, 2),
        "active_clients": total_clientes_ativos,
        "points_issued": pts_emitidos,
    }


@router.get("/weekly-revenue")
def weekly_revenue(db: Session = Depends(get_db), _=Depends(get_current_user)):
    hoje = datetime.now().date()
    resultado = []
    for i in range(6, -1, -1):
        dia = hoje - timedelta(days=i)
        inicio_dia = datetime(dia.year, dia.month, dia.day, 0, 0, 0)
        fim_dia = datetime(dia.year, dia.month, dia.day, 23, 59, 59)
        appts = (
            _scope_appointments(db.query(Appointment), _)
            .filter(
                Appointment.scheduled_at >= inicio_dia,
                Appointment.scheduled_at <= fim_dia,
                Appointment.status == AppointmentStatus.completed,
            )
            .all()
        )
        receita = sum(a.price_charged or a.service.price for a in appts)
        resultado.append({
            "date": dia.strftime("%d/%m"),
            "revenue": round(receita, 2),
            "appointments": len(appts),
        })
    return resultado


@router.get("/alerts")
def alerts(db: Session = Depends(get_db), _=Depends(get_current_user)):
    hoje = datetime.now()
    dia = hoje.date()

    # Aniversários do dia
    birthday_query = db.query(Client)
    if _ is not None and _.role == "professional":
        birthday_query = birthday_query.join(Appointment, Appointment.client_id == Client.id).filter(
            Appointment.professional_id == _.professional_id
        ).distinct()
    aniversariantes = (
        birthday_query
        .filter(
            Client.is_active == True,
            func.strftime("%m-%d", Client.birthdate) == dia.strftime("%m-%d"),
        )
        .all()
    )

    # Clientes Platinum agendados hoje
    inicio_dia = datetime(dia.year, dia.month, dia.day, 0, 0, 0)
    fim_dia = datetime(dia.year, dia.month, dia.day, 23, 59, 59)
    from models.client import LoyaltyTier
    platinum_hoje = (
        _scope_appointments(db.query(Appointment), _)
        .join(Client, Client.id == Appointment.client_id)
        .filter(
            Appointment.scheduled_at >= inicio_dia,
            Appointment.scheduled_at <= fim_dia,
            Appointment.status.notin_([AppointmentStatus.cancelled, AppointmentStatus.no_show]),
            Client.loyalty_tier == LoyaltyTier.platinum,
        )
        .all()
    )

    # Insumos com saldo no/abaixo do mínimo
    low_stock = (
        db.query(Product)
        .filter(Product.is_active == True, Product.stock_qty <= Product.min_stock)
        .order_by(Product.stock_qty)
        .all()
    )

    # Insumos vencendo em até 30 dias (inclui já vencidos)
    limite_validade = (hoje + timedelta(days=30)).date()
    expiring = (
        db.query(Product)
        .filter(
            Product.is_active == True,
            Product.expiry_date.isnot(None),
            Product.expiry_date <= limite_validade,
        )
        .order_by(Product.expiry_date)
        .all()
    )
    if _ is not None and _.role == "professional":
        low_stock = []
        expiring = []

    return {
        "birthdays_today": [
            {"id": c.id, "name": c.name, "code": c.code} for c in aniversariantes
        ],
        "platinum_today": [
            {"appointment_id": a.id, "client_name": a.client.name, "scheduled_at": a.scheduled_at}
            for a in platinum_hoje
        ],
        "low_stock": [
            {
                "id": p.id, "name": p.name, "unit": p.unit,
                "stock_qty": round(p.stock_qty, 2), "min_stock": round(p.min_stock, 2),
            }
            for p in low_stock
        ],
        "expiring_soon": [
            {
                "id": p.id, "name": p.name,
                "expiry_date": p.expiry_date,
                "days_to_expiry": (p.expiry_date - dia).days,
            }
            for p in expiring
        ],
    }


@router.get("/upcoming")
def upcoming_appointments(
    days: int = Query(2, ge=1, le=7),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    amanha = datetime.now().date() + timedelta(days=1)
    ate = amanha + timedelta(days=days - 1)
    inicio = datetime(amanha.year, amanha.month, amanha.day)
    fim = datetime(ate.year, ate.month, ate.day, 23, 59, 59)

    query = db.query(Appointment)
    if current_user.role == "professional":
        if current_user.professional_id is None:
            return []
        query = query.filter(Appointment.professional_id == current_user.professional_id)
    appts = (
        query
        .filter(
            Appointment.scheduled_at >= inicio,
            Appointment.scheduled_at <= fim,
            Appointment.status.notin_([AppointmentStatus.cancelled, AppointmentStatus.no_show]),
        )
        .order_by(Appointment.scheduled_at)
        .all()
    )

    return [
        {
            "id": a.id,
            "scheduled_at": a.scheduled_at,
            "client": {"name": a.client.name, "code": a.client.code, "tier": a.client.loyalty_tier},
            "professional": {"name": a.professional.name},
            "service": {"name": a.service.name},
            "status": a.status,
        }
        for a in appts
    ]
