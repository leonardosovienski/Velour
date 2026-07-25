import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models.appointment import Appointment, AppointmentStatus
from models.client import Client, LoyaltyTier, calculate_tier
from models.loyalty import LoyaltyTransaction, TransactionType
from models.product import Product
from models.professional import Professional
from models.referral import Referral, ReferralStatus
from models.service import Service
from models.service_recipe import ServiceRecipe
from models.stock_movement import StockMovement, StockMovementType
from schemas.appointment import (
    AppointmentCreate, AppointmentResponse, AppointmentStatusUpdate,
    AppointmentComplete, AppointmentDetail,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])

# Serializa checagem-de-conflito + criação para evitar overbooking sob
# requisições concorrentes (a checagem e o INSERT não são atômicos no banco).
_booking_lock = threading.Lock()

# Serializa o fechamento de atendimentos: evita que duas conclusões
# concorrentes do primeiro atendimento de clientes diferentes indicados
# pela mesma pessoa leiam a indicação pendente como não-convertida ao
# mesmo tempo e apliquem os pontos de indicação em duplicidade.
_completion_lock = threading.Lock()

# Tipos de imagem aceitos em upload de fotos (before/after)
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _sniff_image_type(content: bytes) -> Optional[str]:
    """Identifica o tipo da imagem pelos magic bytes, não pelo header Content-Type
    (que é enviado pelo cliente e pode ser falsificado)."""
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None

# Pontos por R$1 gasto
POINTS_PER_BRL = 1
# Pontos para resgate: 100 pts = R$10
POINTS_REDEMPTION_RATE = 0.10
# Desconto máximo por atendimento (50%)
MAX_DISCOUNT_RATIO = 0.5
# Pontos ganhos por indicação convertida
REFERRAL_POINTS_REFERRER = 150
REFERRAL_POINTS_REFERRED = 75

# Desconto automático por tier de fidelidade (sobre o valor base do serviço)
TIER_DISCOUNT_RATES = {
    LoyaltyTier.bronze: 0.0,
    LoyaltyTier.silver: 0.05,
    LoyaltyTier.gold: 0.10,
    LoyaltyTier.platinum: 0.15,
}


def _check_conflict(db: Session, prof_id: int, start: datetime, end: datetime, ignore_id: Optional[int] = None):
    q = (
        db.query(Appointment)
        .filter(
            Appointment.professional_id == prof_id,
            Appointment.status.notin_([AppointmentStatus.cancelled, AppointmentStatus.no_show]),
            Appointment.scheduled_at < end,
            Appointment.ends_at > start,
        )
    )
    if ignore_id:
        q = q.filter(Appointment.id != ignore_id)
    conflict = q.first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Conflito de horário para este profissional",
                "appointment_id": conflict.id,
                "scheduled_at": conflict.scheduled_at.isoformat(),
                "ends_at": conflict.ends_at.isoformat(),
            },
        )


def _apply_loyalty_completion(db: Session, appt: Appointment):
    """Processa pontos, tier e indicações ao concluir um atendimento."""
    client = appt.client
    base_price = appt.price_charged or appt.service.price

    # Tier vigente ANTES de incorporar o gasto deste atendimento (sem downgrade).
    tier_at_service = client.loyalty_tier
    tier_rate = TIER_DISCOUNT_RATES.get(tier_at_service, 0.0)
    tier_discount = base_price * tier_rate

    # Teto absoluto: desconto combinado (tier + pontos) <= 50% do valor base.
    max_total_discount = base_price * MAX_DISCOUNT_RATIO

    # Desconto por resgate de pontos, aplicado DEPOIS do tier e limitado ao que
    # sobra do teto. Os pontos usados são debitados integralmente (mesmo que o
    # desconto efetivo seja menor por causa do teto).
    points_discount = 0.0
    if appt.discount_points_used > 0:
        points_discount = appt.discount_points_used * POINTS_REDEMPTION_RATE
        remaining_cap = max(max_total_discount - tier_discount, 0.0)
        points_discount = min(points_discount, remaining_cap)

        client.loyalty_points -= appt.discount_points_used
        tx_redeem = LoyaltyTransaction(
            client_id=client.id,
            appointment_id=appt.id,
            type=TransactionType.redeemed,
            points=-appt.discount_points_used,
            description=f"Resgate de pontos — atendimento #{appt.id}",
        )
        db.add(tx_redeem)

    final_price = max(base_price - tier_discount - points_discount, 0.0)

    # Pontos ganhos pelo atendimento (sobre o valor efetivamente pago)
    points_earned = int(final_price) * POINTS_PER_BRL
    if appt.service.points_reward > 0:
        points_earned = appt.service.points_reward

    client.loyalty_points += points_earned
    client.total_spent += final_price
    client.total_visits += 1

    appt.points_awarded = points_earned
    appt.price_charged = final_price
    appt.tier_at_service = tier_at_service
    appt.tier_discount_amount = tier_discount

    tx_earn = LoyaltyTransaction(
        client_id=client.id,
        appointment_id=appt.id,
        type=TransactionType.earned_appointment,
        points=points_earned,
        description=f"Atendimento concluído — {appt.service.name}",
    )
    db.add(tx_earn)

    # Recalcular tier
    client.loyalty_tier = calculate_tier(client.total_spent)

    # Verificar se indicação pendente deve ser convertida (primeiro atendimento)
    # Exclui o appointment atual porque o autoflush do SQLAlchemy já o veria como completed
    total_completed = (
        db.query(Appointment)
        .filter(
            Appointment.client_id == client.id,
            Appointment.status == AppointmentStatus.completed,
            Appointment.id != appt.id,
        )
        .count()
    )
    if total_completed == 0:  # este é o primeiro atendimento concluído
        pending_ref = (
            db.query(Referral)
            .filter(Referral.referred_id == client.id, Referral.status == ReferralStatus.pending)
            .first()
        )
        if pending_ref:
            pending_ref.status = ReferralStatus.converted
            pending_ref.converted_at = datetime.now()
            pending_ref.points_awarded_referrer = REFERRAL_POINTS_REFERRER
            pending_ref.points_awarded_referred = REFERRAL_POINTS_REFERRED

            referrer = db.query(Client).filter(Client.id == pending_ref.referrer_id).first()
            if referrer:
                referrer.loyalty_points += REFERRAL_POINTS_REFERRER
                db.add(LoyaltyTransaction(
                    client_id=referrer.id,
                    referral_id=pending_ref.id,
                    type=TransactionType.earned_referral,
                    points=REFERRAL_POINTS_REFERRER,
                    description=f"Indicação convertida — {client.name}",
                ))

            client.loyalty_points += REFERRAL_POINTS_REFERRED
            db.add(LoyaltyTransaction(
                client_id=client.id,
                referral_id=pending_ref.id,
                type=TransactionType.earned_referral,
                points=REFERRAL_POINTS_REFERRED,
                description="Bônus de boas-vindas por indicação",
            ))


def _apply_stock_deduction(db: Session, appt: Appointment, overrides: Optional[list] = None):
    """
    Dá baixa nos insumos da ficha técnica do serviço ao concluir o atendimento.

    Regras (decididas para o MVP):
    - A receita (ServiceRecipe) define a quantidade-padrão por insumo.
    - `overrides` (product_id + actual_qty) substituem a dosagem-padrão e podem
      incluir insumos fora da receita (ex.: produto extra usado na coloração).
      actual_qty == 0 significa "não consumiu" → ignora aquele insumo.
    - A dedução é INCONDICIONAL: a operação não pode travar no balcão. Se o saldo
      ficar <= 0, a transação conclui normalmente e o alerta de reposição é
      disparado depois pelo dashboard (stock_qty <= min_stock).
    - Cada baixa registra uma StockMovement (ledger append-only).
    """
    # Quantidade-padrão da ficha técnica
    consumo = {
        r.product_id: r.qty_consumed
        for r in db.query(ServiceRecipe).filter(ServiceRecipe.service_id == appt.service_id).all()
    }

    # Overrides sobrescrevem a dosagem (e podem adicionar insumos fora da receita)
    for ov in (overrides or []):
        consumo[ov.product_id] = ov.actual_qty

    for product_id, qty in consumo.items():
        if qty <= 0:
            continue  # nada a consumir

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=422,
                detail=f"Insumo {product_id} informado no consumo não existe",
            )

        qty_before = product.stock_qty
        qty_after = qty_before - qty  # pode ficar <= 0; alerta cuida disso depois
        product.stock_qty = qty_after

        db.add(StockMovement(
            product_id=product.id,
            appointment_id=appt.id,
            type=StockMovementType.consumption,
            qty=-qty,
            qty_before=qty_before,
            qty_after=qty_after,
            description=f"Consumo — {appt.service.name} (atendimento #{appt.id})",
        ))


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("", response_model=List[AppointmentDetail])
def list_appointments(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[AppointmentStatus] = None,
    professional_id: Optional[int] = None,
    client_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(Appointment)
    if date_from:
        q = q.filter(Appointment.scheduled_at >= date_from)
    if date_to:
        q = q.filter(Appointment.scheduled_at <= date_to)
    if status:
        q = q.filter(Appointment.status == status)
    if professional_id:
        q = q.filter(Appointment.professional_id == professional_id)
    if client_id:
        q = q.filter(Appointment.client_id == client_id)
    return q.order_by(Appointment.scheduled_at).offset(offset).limit(limit).all()


@router.get("/{appt_id}", response_model=AppointmentDetail)
def get_appointment(appt_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    return appt


@router.post("", response_model=AppointmentResponse, status_code=201)
def create_appointment(body: AppointmentCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == body.client_id, Client.is_active == True).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    prof = db.query(Professional).filter(Professional.id == body.professional_id, Professional.is_active == True).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    service = db.query(Service).filter(Service.id == body.service_id, Service.is_active == True).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    ends_at = body.scheduled_at + timedelta(minutes=service.duration_minutes)

    with _booking_lock:
        _check_conflict(db, body.professional_id, body.scheduled_at, ends_at)

        appt = Appointment(
            client_id=body.client_id,
            professional_id=body.professional_id,
            service_id=body.service_id,
            scheduled_at=body.scheduled_at,
            ends_at=ends_at,
            occasion=body.occasion,
            notes=body.notes,
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)
    return appt


@router.patch("/{appt_id}/status", response_model=AppointmentResponse)
def update_status(
    appt_id: int,
    body: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    if body.status == AppointmentStatus.completed:
        raise HTTPException(
            status_code=422,
            detail="Para concluir use POST /appointments/{id}/complete com os dados de cobrança",
        )
    appt.status = body.status
    db.commit()
    db.refresh(appt)
    return appt


@router.post("/{appt_id}/complete", response_model=AppointmentResponse)
def complete_appointment(
    appt_id: int,
    body: AppointmentComplete,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    with _completion_lock:
        appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
        if not appt:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado")
        if appt.status == AppointmentStatus.completed:
            raise HTTPException(status_code=409, detail="Atendimento já concluído")
        if appt.status in (AppointmentStatus.cancelled, AppointmentStatus.no_show):
            raise HTTPException(status_code=422, detail="Não é possível concluir um atendimento cancelado")

        # Validar resgate de pontos
        if body.discount_points_used > 0:
            if body.discount_points_used % 100 != 0:
                raise HTTPException(status_code=422, detail="Resgate deve ser múltiplo de 100 pontos")
            if body.discount_points_used > appt.client.loyalty_points:
                raise HTTPException(status_code=422, detail="Pontos insuficientes")

        appt.price_charged = body.price_charged
        appt.discount_points_used = body.discount_points_used
        appt.photo_before_url = body.photo_before_url
        appt.photo_after_url = body.photo_after_url
        appt.formula_used = body.formula_used
        if body.notes:
            appt.notes = body.notes
        appt.status = AppointmentStatus.completed

        # Mesma transação atômica: fidelidade + baixa de estoque.
        # Qualquer exceção aqui aborta o commit inteiro (Unit of Work).
        _apply_loyalty_completion(db, appt)
        _apply_stock_deduction(db, appt, body.recipe_overrides)

        db.commit()
        db.refresh(appt)
    return appt


async def _save_photo(photo: UploadFile, upload_dir: Path) -> str:
    content = await photo.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="Imagem muito grande (máximo 5MB)")

    sniffed_type = _sniff_image_type(content)
    if sniffed_type is None:
        raise HTTPException(
            status_code=422,
            detail="Formato de imagem não suportado. Envie JPEG, PNG ou WebP.",
        )

    ext = ALLOWED_IMAGE_TYPES[sniffed_type]
    fname = f"{uuid4().hex}{ext}"
    (upload_dir / fname).write_bytes(content)
    return f"/uploads/{fname}"


@router.post("/{appt_id}/photos")
async def upload_photos(
    appt_id: int,
    photo_before: Optional[UploadFile] = File(None),
    photo_after: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    if photo_before and photo_before.filename:
        appt.photo_before_url = await _save_photo(photo_before, upload_dir)

    if photo_after and photo_after.filename:
        appt.photo_after_url = await _save_photo(photo_after, upload_dir)

    db.commit()
    db.refresh(appt)
    return {"photo_before_url": appt.photo_before_url, "photo_after_url": appt.photo_after_url}


@router.delete("/{appt_id}", status_code=204)
def cancel_appointment(appt_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    if appt.status == AppointmentStatus.completed:
        raise HTTPException(status_code=409, detail="Não é possível cancelar um atendimento concluído")
    appt.status = AppointmentStatus.cancelled
    db.commit()
