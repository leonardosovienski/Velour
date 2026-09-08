from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from database import SessionLocal, system_scope
from config import settings
from runtime_guard import runtime_guard
from domain_locks import serialized_mutation
from models.tenant import Tenant
from models.client import Client
from models.loyalty import LoyaltyTransaction, TransactionType

BIRTHDAY_POINTS = 100

scheduler = AsyncIOScheduler()


@serialized_mutation
def _run_birthday_job():
    if settings.environment == "production":
        runtime_guard.check()
    hoje = datetime.now()
    inicio_mes = datetime(hoje.year, hoje.month, 1)
    db: Session = SessionLocal()
    try:
        with system_scope(db):
            clientes = (
                db.query(Client)
                .join(Tenant, Tenant.id == Client.tenant_id)
                .filter(Tenant.is_active == True)
                .filter(
                    Client.is_active == True,
                    Client.birthdate.isnot(None),
                )
                .all()
            )
            for client in clientes:
                if client.birthdate.month != hoje.month or client.birthdate.day != hoje.day:
                    continue
                # Idempotência: não concede se já existe earned_birthday no mês atual
                already = (
                    db.query(LoyaltyTransaction)
                    .filter(
                        LoyaltyTransaction.client_id == client.id,
                        LoyaltyTransaction.type == TransactionType.earned_birthday,
                        LoyaltyTransaction.created_at >= inicio_mes,
                    )
                    .first()
                )
                if already:
                    continue

                client.loyalty_points += BIRTHDAY_POINTS
                db.add(LoyaltyTransaction(
                    client_id=client.id,
                    tenant_id=client.tenant_id,
                    type=TransactionType.earned_birthday,
                    points=BIRTHDAY_POINTS,
                    description=f"Bônus de aniversário — {hoje.year}",
                ))
            db.commit()
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(_run_birthday_job, "cron", hour=8, minute=0, id="birthday_points")
    scheduler.start()
