from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_manager
from database import get_db
from models.audit_log import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource: str
    status_code: int
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(require_manager),
):
    query = db.query(AuditLog)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action.upper())
    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
