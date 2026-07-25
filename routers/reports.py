from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models.appointment import Appointment, AppointmentStatus
from models.client import Client, LoyaltyTier
from models.loyalty import LoyaltyTransaction, TransactionType
from models.professional import Professional
from models.referral import Referral, ReferralStatus
from models.service import Service, ServiceCategory

router = APIRouter(prefix="/reports", tags=["reports"])


def _parse_period(period_start: Optional[str], period_end: Optional[str]):
    hoje = datetime.now()
    inicio = datetime.fromisoformat(period_start) if period_start else datetime(hoje.year, hoje.month, 1)
    fim = datetime.fromisoformat(period_end) if period_end else datetime(hoje.year, hoje.month + 1, 1) if hoje.month < 12 else datetime(hoje.year + 1, 1, 1)
    return inicio, fim


@router.get("/revenue")
def revenue_report(
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    professional_id: Optional[int] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    inicio, fim = _parse_period(period_start, period_end)

    q = (
        db.query(Appointment)
        .filter(
            Appointment.scheduled_at >= inicio,
            Appointment.scheduled_at < fim,
            Appointment.status == AppointmentStatus.completed,
        )
    )
    if professional_id:
        q = q.filter(Appointment.professional_id == professional_id)
    if category_id:
        q = q.join(Service).filter(Service.category_id == category_id)

    appts = q.all()
    receita_total = sum(a.price_charged or a.service.price for a in appts)

    # Por profissional
    por_prof: dict = {}
    for a in appts:
        nome = a.professional.name
        por_prof.setdefault(nome, {"appointments": 0, "revenue": 0.0})
        por_prof[nome]["appointments"] += 1
        por_prof[nome]["revenue"] += a.price_charged or a.service.price

    # Por categoria
    por_cat: dict = {}
    for a in appts:
        nome = a.service.category.name
        por_cat.setdefault(nome, {"appointments": 0, "revenue": 0.0})
        por_cat[nome]["appointments"] += 1
        por_cat[nome]["revenue"] += a.price_charged or a.service.price

    # Por gênero do cliente
    por_genero: dict = {}
    for a in appts:
        g = a.client.gender.value
        por_genero.setdefault(g, {"appointments": 0, "revenue": 0.0})
        por_genero[g]["appointments"] += 1
        por_genero[g]["revenue"] += a.price_charged or a.service.price

    return {
        "period_start": inicio.isoformat(),
        "period_end": fim.isoformat(),
        "total_revenue": round(receita_total, 2),
        "total_appointments": len(appts),
        "by_professional": [{"name": k, **v, "revenue": round(v["revenue"], 2)} for k, v in por_prof.items()],
        "by_category": [{"name": k, **v, "revenue": round(v["revenue"], 2)} for k, v in por_cat.items()],
        "by_gender": [{"gender": k, **v, "revenue": round(v["revenue"], 2)} for k, v in por_genero.items()],
    }


@router.get("/clients")
def client_report(
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    inicio, fim = _parse_period(period_start, period_end)

    novos = db.query(Client).filter(Client.created_at >= inicio, Client.created_at < fim).count()

    # Churn: sem agendamento concluído nos últimos 60 dias
    cutoff_churn = datetime.now() - timedelta(days=60)
    ids_ativos = (
        db.query(Appointment.client_id)
        .filter(Appointment.status == AppointmentStatus.completed, Appointment.scheduled_at >= cutoff_churn)
        .distinct()
        .subquery()
    )
    churn_count = db.query(Client).filter(Client.is_active == True, ~Client.id.in_(ids_ativos)).count()

    # Distribuição por tier
    tier_dist = {}
    for tier in LoyaltyTier:
        tier_dist[tier.value] = db.query(Client).filter(Client.loyalty_tier == tier, Client.is_active == True).count()

    return {
        "period_start": inicio.isoformat(),
        "period_end": fim.isoformat(),
        "new_clients": novos,
        "churn_risk_count": churn_count,
        "tier_distribution": tier_dist,
        "total_active": db.query(Client).filter(Client.is_active == True).count(),
    }


@router.get("/loyalty-monthly")
def loyalty_monthly(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    hoje = datetime.now()
    resultado = []
    for i in range(months - 1, -1, -1):
        mes_ref = hoje.month - i
        ano_ref = hoje.year + (mes_ref - 1) // 12
        mes_ref = ((mes_ref - 1) % 12) + 1
        inicio_mes = datetime(ano_ref, mes_ref, 1)
        if mes_ref == 12:
            fim_mes = datetime(ano_ref + 1, 1, 1)
        else:
            fim_mes = datetime(ano_ref, mes_ref + 1, 1)

        emitidos = (
            db.query(func.sum(LoyaltyTransaction.points))
            .filter(LoyaltyTransaction.created_at >= inicio_mes, LoyaltyTransaction.created_at < fim_mes, LoyaltyTransaction.points > 0)
            .scalar() or 0
        )
        resgatados = abs(
            db.query(func.sum(LoyaltyTransaction.points))
            .filter(LoyaltyTransaction.created_at >= inicio_mes, LoyaltyTransaction.created_at < fim_mes, LoyaltyTransaction.type == TransactionType.redeemed)
            .scalar() or 0
        )

        resultado.append({
            "month": inicio_mes.strftime("%b/%Y"),
            "points_issued": emitidos,
            "points_redeemed": resgatados,
        })

    return resultado


@router.get("/referrals-monthly")
def referrals_monthly(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    hoje = datetime.now()
    resultado = []
    for i in range(months - 1, -1, -1):
        mes_ref = hoje.month - i
        ano_ref = hoje.year + (mes_ref - 1) // 12
        mes_ref = ((mes_ref - 1) % 12) + 1
        inicio_mes = datetime(ano_ref, mes_ref, 1)
        if mes_ref == 12:
            fim_mes = datetime(ano_ref + 1, 1, 1)
        else:
            fim_mes = datetime(ano_ref, mes_ref + 1, 1)

        criadas_no_mes = db.query(Referral).filter(Referral.created_at >= inicio_mes, Referral.created_at < fim_mes).count()
        convertidas = db.query(Referral).filter(
            Referral.converted_at >= inicio_mes, Referral.converted_at < fim_mes, Referral.status == ReferralStatus.converted
        ).count()
        pts_investidos = (
            db.query(func.sum(Referral.points_awarded_referrer + Referral.points_awarded_referred))
            .filter(Referral.converted_at >= inicio_mes, Referral.converted_at < fim_mes)
            .scalar() or 0
        )
        total_existentes = db.query(Referral).filter(Referral.created_at < fim_mes).count()

        resultado.append({
            "month": inicio_mes.strftime("%b/%Y"),
            "referrals_created": criadas_no_mes,
            "referrals_converted": convertidas,
            "points_invested": pts_investidos,
            "conversion_rate": round(convertidas / total_existentes, 4) if total_existentes else 0.0,
        })

    return resultado
