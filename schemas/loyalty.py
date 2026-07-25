from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel

from models.loyalty import TransactionType
from models.client import LoyaltyTier


class LoyaltyTransactionResponse(BaseModel):
    id: int
    client_id: int
    appointment_id: Optional[int]
    referral_id: Optional[int]
    type: TransactionType
    points: int
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TierDistribution(BaseModel):
    tier: LoyaltyTier
    count: int


class LoyaltyOverview(BaseModel):
    total_points_in_circulation: int
    points_issued_this_month: int
    points_redeemed_this_month: int
    tier_distribution: List[TierDistribution]
    top_clients: List[Dict]
