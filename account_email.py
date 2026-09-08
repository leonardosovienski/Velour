"""Account e-mails; reset secrets are never written to logs or persisted raw."""
from urllib.parse import urlencode

from config import settings
from email_service import send_email


def send_password_reset(email: str, name: str, token: str) -> bool:
    link = f"{settings.frontend_url.rstrip('/')}/reset-password?{urlencode({'token': token})}"
    return send_email(
        email, "Redefina sua senha — Velour",
        f"Olá, {name}!\n\nPara criar uma nova senha, abra:\n{link}\n\n"
        f"Este link expira em {settings.password_reset_expire_minutes} minutos e pode ser usado uma única vez.\n\n"
        "Se você não pediu a alteração, ignore este e-mail. Sua senha continuará a mesma.\n\n— Velour",
    )
