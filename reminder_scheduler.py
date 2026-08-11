import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from database import SessionLocal
from email_service import send_appointment_reminder
from logging_config import log_with_fields
from models.appointment import Appointment, AppointmentStatus

logger = logging.getLogger("velour.reminder_scheduler")
scheduler = AsyncIOScheduler()

# Lembrete enviado uma vez por atendimento, para agendamentos que ocorrem
# entre 24h e 25h à frente do horário de execução do job.
REMINDER_WINDOW_HOURS = 24


def _run_reminder_job():
    now = datetime.now()
    window_start = now + timedelta(hours=REMINDER_WINDOW_HOURS)
    window_end = window_start + timedelta(hours=1)
    db: Session = SessionLocal()
    try:
        appointments = (
            db.query(Appointment)
            .filter(
                Appointment.status.in_([AppointmentStatus.scheduled, AppointmentStatus.confirmed]),
                Appointment.reminder_sent == False,  # noqa: E712
                Appointment.scheduled_at >= window_start,
                Appointment.scheduled_at < window_end,
            )
            .all()
        )
        sent = 0
        for appt in appointments:
            if send_appointment_reminder(appt):
                appt.reminder_sent = True
                sent += 1
        db.commit()
        log_with_fields(
            logger, logging.INFO, "reminder_job_completed",
            candidates=len(appointments), sent=sent,
        )
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(_run_reminder_job, "cron", minute=0, id="appointment_reminders")
    scheduler.start()
