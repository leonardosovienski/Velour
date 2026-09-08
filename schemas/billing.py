from datetime import datetime

from pydantic import BaseModel


class BillingStatus(BaseModel):
    tenant_id: int
    tenant_name: str
    subscription_status: str
    trial_ends_at: datetime | None
    current_period_end: datetime | None
    past_due_since: datetime | None
    access_allowed: bool
    configured: bool
    can_manage_billing: bool
    has_billing_customer: bool


class HostedSession(BaseModel):
    url: str
