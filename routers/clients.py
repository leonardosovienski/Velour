import threading
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from models.client import Client, LoyaltyTier, calculate_tier, generate_referral_code
from models.appointment import Appointment, AppointmentStatus
from schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientBriefing, LastAppointmentBrief

router = APIRouter(prefix="/clients", tags=["clients"])

# Serializa a geração de código VLR-xxxxx e referral_code para evitar
# colisões sob criação concorrente de clientes (nenhum dos dois é atômico
# com o INSERT no banco).
_client_code_lock = threading.Lock()


def _next_vlr_code(db: Session) -> str:
    last = db.query(Client).order_by(Client.id.desc()).first()
    seq = (last.id if last else 0) + 1
    return f"VLR-{seq:05d}"


def _spent_to_next_tier(total_spent: float, tier: LoyaltyTier) -> Optional[float]:
    thresholds = {
        LoyaltyTier.bronze:   500,
        LoyaltyTier.silver:   1500,
        LoyaltyTier.gold:     3000,
        LoyaltyTier.platinum: None,
    }
    target = thresholds[tier]
    return round(target - total_spent, 2) if target is not None else None


@router.get("", response_model=List[ClientResponse])
def list_clients(
    tier: Optional[LoyaltyTier] = None,
    gender: Optional[str] = None,
    inactive_days: Optional[int] = None,
    is_active: bool = True,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(Client).filter(Client.is_active == is_active)
    if tier:
        q = q.filter(Client.loyalty_tier == tier)
    if gender:
        q = q.filter(Client.gender == gender)
    if inactive_days:
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=inactive_days)
        # clientes sem agendamentos concluídos após o cutoff
        active_ids = (
            db.query(Appointment.client_id)
            .filter(Appointment.status == AppointmentStatus.completed)
            .filter(Appointment.scheduled_at >= cutoff)
            .subquery()
        )
        q = q.filter(~Client.id.in_(active_ids))
    return q.offset(offset).limit(limit).all()


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.get("/{client_id}/briefing", response_model=ClientBriefing)
def get_briefing(client_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    last_appt = (
        db.query(Appointment)
        .filter(Appointment.client_id == client_id)
        .filter(Appointment.status == AppointmentStatus.completed)
        .order_by(Appointment.scheduled_at.desc())
        .first()
    )

    last_brief = None
    if last_appt:
        last_brief = LastAppointmentBrief(
            date=last_appt.scheduled_at,
            professional_name=last_appt.professional.name,
            service_name=last_appt.service.name,
            formula_used=last_appt.formula_used,
            notes=last_appt.notes,
        )

    return ClientBriefing(
        id=client.id,
        code=client.code,
        name=client.name,
        loyalty_tier=client.loyalty_tier,
        loyalty_points=client.loyalty_points,
        total_spent=client.total_spent,
        total_visits=client.total_visits,
        first_visit=client.first_visit,
        preferred_drink=client.preferred_drink,
        music_preference=client.music_preference,
        temperature_preference=client.temperature_preference,
        chat_preference=client.chat_preference,
        allergies=client.allergies,
        notes=client.notes,
        last_appointment=last_brief,
        spent_to_next_tier=_spent_to_next_tier(client.total_spent, client.loyalty_tier),
    )


@router.post("", response_model=ClientResponse, status_code=201)
def create_client(body: ClientCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    referred_by_id = None
    if body.referral_code_used:
        referrer = db.query(Client).filter(Client.referral_code == body.referral_code_used).first()
        if not referrer:
            raise HTTPException(status_code=404, detail="Código de indicação inválido")
        referred_by_id = referrer.id

    with _client_code_lock:
        referral_code = generate_referral_code()
        while db.query(Client).filter(Client.referral_code == referral_code).first():
            referral_code = generate_referral_code()

        data = body.model_dump(exclude={"referral_code_used"})
        client = Client(
            **data,
            code=_next_vlr_code(db),
            referral_code=referral_code,
            referred_by_id=referred_by_id,
            first_visit=date.today(),
        )
        db.add(client)
        db.flush()

        if referred_by_id:
            from models.referral import Referral, ReferralStatus
            ref = Referral(referrer_id=referred_by_id, referred_id=client.id)
            db.add(ref)

        db.commit()
        db.refresh(client)
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, body: ClientUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def deactivate_client(client_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    client.is_active = False
    db.commit()
