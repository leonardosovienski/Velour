from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models.client import Client
from models.referral import Referral, ReferralStatus
from schemas.referral import ReferralResponse

router = APIRouter(prefix="/referrals", tags=["referrals"])


@router.get("", response_model=List[ReferralResponse])
def list_referrals(
    status: Optional[ReferralStatus] = None,
    referrer_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(Referral)
    if status:
        q = q.filter(Referral.status == status)
    if referrer_id:
        q = q.filter(Referral.referrer_id == referrer_id)
    return q.order_by(Referral.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/ranking")
def referral_ranking(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Top indicadores de todos os tempos por indicações convertidas."""
    rows = (
        db.query(
            Client.id,
            Client.name,
            Client.referral_code,
            func.count(Referral.id).label("conversions"),
        )
        .join(Referral, Referral.referrer_id == Client.id)
        .filter(Referral.status == ReferralStatus.converted)
        .group_by(Client.id)
        .order_by(func.count(Referral.id).desc())
        .limit(10)
        .all()
    )
    return [
        {"client_id": r.id, "name": r.name, "code": r.referral_code, "conversions": r.conversions}
        for r in rows
    ]
