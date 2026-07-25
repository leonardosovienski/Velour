from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models.referral import ReferralStatus


class ReferralResponse(BaseModel):
    id: int
    referrer_id: int
    referred_id: int
    status: ReferralStatus
    points_awarded_referrer: int
    points_awarded_referred: int
    converted_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
