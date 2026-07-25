from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from database import SessionLocal
from models.client import Client
from models.loyalty import LoyaltyTransaction, TransactionType

BIRTHDAY_POINTS = 100

scheduler = AsyncIOScheduler()


def _run_birthday_job():
    hoje = datetime.now()
    inicio_mes = datetime(hoje.year, hoje.month, 1)
    db: Session = SessionLocal()
    try:
        clientes = (
            db.query(Client)
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
