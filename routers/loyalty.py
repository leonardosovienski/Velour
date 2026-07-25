from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models.client import Client, LoyaltyTier
from models.loyalty import LoyaltyTransaction, TransactionType
from schemas.loyalty import LoyaltyTransactionResponse, LoyaltyOverview, TierDistribution

router = APIRouter(prefix="/loyalty", tags=["loyalty"])


@router.get("/transactions", response_model=List[LoyaltyTransactionResponse])
def list_transactions(
    client_id: Optional[int] = None,
    type: Optional[TransactionType] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(LoyaltyTransaction)
    if client_id:
        q = q.filter(LoyaltyTransaction.client_id == client_id)
    if type:
        q = q.filter(LoyaltyTransaction.type == type)
    if date_from:
        q = q.filter(LoyaltyTransaction.created_at >= date_from)
    if date_to:
        q = q.filter(LoyaltyTransaction.created_at <= date_to)
    return q.order_by(LoyaltyTransaction.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/overview", response_model=LoyaltyOverview)
def loyalty_overview(db: Session = Depends(get_db), _=Depends(get_current_user)):
    hoje = datetime.now()
    inicio_mes = datetime(hoje.year, hoje.month, 1)

    total_pts = db.query(func.sum(Client.loyalty_points)).scalar() or 0

    pts_emitidos_mes = (
        db.query(func.sum(LoyaltyTransaction.points))
        .filter(
            LoyaltyTransaction.created_at >= inicio_mes,
            LoyaltyTransaction.points > 0,
        )
        .scalar() or 0
    )

    pts_resgatados_mes = abs(
        db.query(func.sum(LoyaltyTransaction.points))
        .filter(
            LoyaltyTransaction.created_at >= inicio_mes,
            LoyaltyTransaction.type == TransactionType.redeemed,
        )
        .scalar() or 0
    )

    tier_dist = []
    for tier in LoyaltyTier:
        count = db.query(Client).filter(Client.loyalty_tier == tier, Client.is_active == True).count()
        tier_dist.append(TierDistribution(tier=tier, count=count))

    top_clients = (
        db.query(Client)
        .filter(Client.is_active == True)
        .order_by(Client.loyalty_points.desc())
        .limit(10)
        .all()
    )
    top_list = [
        {"id": c.id, "code": c.code, "name": c.name, "tier": c.loyalty_tier, "points": c.loyalty_points}
        for c in top_clients
    ]

    return LoyaltyOverview(
        total_points_in_circulation=total_pts,
        points_issued_this_month=pts_emitidos_mes,
        points_redeemed_this_month=pts_resgatados_mes,
        tier_distribution=tier_dist,
        top_clients=top_list,
    )
