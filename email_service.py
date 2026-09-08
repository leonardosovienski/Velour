"""Envio de e-mails transacionais (confirmação e lembrete de agendamento).

Se SMTP_HOST não estiver configurado, o envio é pulado silenciosamente
(apenas logado) — assim dev/local funciona sem servidor de e-mail e a
aplicação nunca falha por causa de notificação.
"""
import logging
import smtplib
from email.message import EmailMessage

from config import settings

logger = logging.getLogger("velour.email")


def is_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from)


def send_email(to: str, subject: str, body: str) -> bool:
    if not to:
        return False
    if not is_configured():
        logger.info("SMTP não configurado — envio ignorado")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return True
    except Exception as exc:
        # SMTP exception messages can contain addresses and provider replies.
        logger.error("Falha ao enviar e-mail (%s)", type(exc).__name__)
        return False


def send_appointment_confirmation(appt) -> bool:
    client = appt.client
    if not client or not client.email:
        return False
    quando = appt.scheduled_at.strftime("%d/%m/%Y às %H:%M")
    service_name = appt.service.name if appt.service else "seu horário"
    subject = "Agendamento confirmado — Velour"
    body = (
        f"Olá, {client.name}!\n\n"
        f"Seu agendamento para {service_name} foi confirmado para {quando}.\n\n"
        "Se precisar remarcar ou cancelar, entre em contato com o salão.\n\n"
        "— Velour"
    )
    return send_email(client.email, subject, body)


def send_appointment_reminder(appt) -> bool:
    client = appt.client
    if not client or not client.email:
        return False
    quando = appt.scheduled_at.strftime("%d/%m/%Y às %H:%M")
    service_name = appt.service.name if appt.service else "seu horário"
    subject = "Lembrete: seu horário é amanhã — Velour"
    body = (
        f"Olá, {client.name}!\n\n"
        f"Passando para lembrar do seu agendamento de {service_name} em {quando}.\n\n"
        "Até breve!\n\n"
        "— Velour"
    )
    return send_email(client.email, subject, body)
