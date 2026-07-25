from typing import List, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from models.professional import Professional
from models.appointment import Appointment, AppointmentStatus
from models.client import Client
from schemas.professional import ProfessionalCreate, ProfessionalUpdate, ProfessionalResponse

router = APIRouter(prefix="/professionals", tags=["professionals"])


@router.get("", response_model=List[ProfessionalResponse])
def list_professionals(
    is_active: bool = True,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return db.query(Professional).filter(Professional.is_active == is_active).all()


@router.get("/{prof_id}", response_model=ProfessionalResponse)
def get_professional(prof_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    prof = db.query(Professional).filter(Professional.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return prof


@router.get("/{prof_id}/stats")
def professional_stats(prof_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    prof = db.query(Professional).filter(Professional.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    hoje = datetime.now()
    inicio_mes = datetime(hoje.year, hoje.month, 1)

    appts_mes = (
        db.query(Appointment)
        .filter(
            Appointment.professional_id == prof_id,
            Appointment.scheduled_at >= inicio_mes,
            Appointment.status == AppointmentStatus.completed,
        )
        .all()
    )

    receita_mes = sum(a.price_charged or a.service.price for a in appts_mes)
    ticket_medio = receita_mes / len(appts_mes) if appts_mes else 0
    comissao_mes = receita_mes * prof.commission_rate

    servicos: dict = {}
    for a in appts_mes:
        servicos[a.service.name] = servicos.get(a.service.name, 0) + 1
    servico_top = max(servicos, key=lambda k: servicos[k]) if servicos else None

    return {
        "professional_id": prof_id,
        "name": prof.name,
        "appointments_this_month": len(appts_mes),
        "revenue_this_month": round(receita_mes, 2),
        "commission_this_month": round(comissao_mes, 2),
        "average_ticket": round(ticket_medio, 2),
        "top_service": servico_top,
    }


@router.get("/{prof_id}/dashboard")
def professional_dashboard(prof_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """
    Painel do profissional: progresso da meta financeira do mês +
    clientes inativos (que ultrapassaram a própria cadência histórica de retorno).
    """
    prof = db.query(Professional).filter(Professional.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    hoje = datetime.now()
    inicio_mes = datetime(hoje.year, hoje.month, 1)

    # ── Meta financeira do mês ────────────────────────────────────────────────
    appts_mes = (
        db.query(Appointment)
        .filter(
            Appointment.professional_id == prof_id,
            Appointment.scheduled_at >= inicio_mes,
            Appointment.status == AppointmentStatus.completed,
        )
        .all()
    )
    receita_mes = sum(a.price_charged or a.service.price for a in appts_mes)
    meta = prof.monthly_goal or 0.0
    progresso = round(receita_mes / meta, 4) if meta > 0 else None

    # ── Clientes inativos por cadência ────────────────────────────────────────
    # "Cliente do profissional" = quem já concluiu atendimento com ele.
    # Cadência = média de dias entre os atendimentos concluídos desse cliente
    # com este profissional (exige >= 2 atendimentos para haver histórico).
    historico = (
        db.query(Appointment)
        .filter(
            Appointment.professional_id == prof_id,
            Appointment.status == AppointmentStatus.completed,
        )
        .order_by(Appointment.scheduled_at)
        .all()
    )
    por_cliente: dict = defaultdict(list)
    for a in historico:
        por_cliente[a.client_id].append(a.scheduled_at)

    inativos = []
    for client_id, datas in por_cliente.items():
        if len(datas) < 2:
            continue  # sem histórico suficiente para uma média
        datas.sort()
        gaps = [(datas[i] - datas[i - 1]).days for i in range(1, len(datas))]
        cadencia = sum(gaps) / len(gaps)
        dias_desde_ultimo = (hoje - datas[-1]).days
        if dias_desde_ultimo > cadencia:
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client or not client.is_active:
                continue
            inativos.append({
                "client_id": client.id,
                "name": client.name,
                "code": client.code,
                "tier": client.loyalty_tier,
                "last_visit": datas[-1],
                "avg_cadence_days": round(cadencia, 1),
                "days_since_last": dias_desde_ultimo,
                "overdue_by_days": round(dias_desde_ultimo - cadencia, 1),
            })

    inativos.sort(key=lambda c: c["overdue_by_days"], reverse=True)

    return {
        "professional_id": prof_id,
        "name": prof.name,
        "monthly_goal": {
            "target": round(meta, 2),
            "revenue": round(receita_mes, 2),
            "commission": round(receita_mes * prof.commission_rate, 2),
            "progress": progresso,                       # None se não houver meta definida
            "remaining": round(max(meta - receita_mes, 0.0), 2) if meta > 0 else None,
        },
        "inactive_clients": inativos,
    }


@router.post("", response_model=ProfessionalResponse, status_code=201)
def create_professional(body: ProfessionalCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    prof = Professional(**body.model_dump())
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return prof


@router.patch("/{prof_id}", response_model=ProfessionalResponse)
def update_professional(prof_id: int, body: ProfessionalUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    prof = db.query(Professional).filter(Professional.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(prof, field, value)
    db.commit()
    db.refresh(prof)
    return prof


@router.delete("/{prof_id}", status_code=204)
def deactivate_professional(prof_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    prof = db.query(Professional).filter(Professional.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    prof.is_active = False
    db.commit()
