from dataclasses import replace
from unittest.mock import MagicMock, patch

import email_service


def test_send_email_sem_smtp_configurado_retorna_false(monkeypatch):
    monkeypatch.setattr(email_service, "settings", replace(email_service.settings, smtp_host=""))
    assert email_service.send_email("cliente@teste.com", "Assunto", "Corpo") is False


def test_send_email_sem_destinatario_retorna_false():
    assert email_service.send_email("", "Assunto", "Corpo") is False


def test_send_email_configurado_chama_smtp(monkeypatch):
    monkeypatch.setattr(email_service, "settings", replace(
        email_service.settings,
        smtp_host="smtp.teste.com",
        smtp_from="Velour <no-reply@velour.com>",
        smtp_port=587,
        smtp_user="",
        smtp_use_tls=True,
    ))

    smtp_instance = MagicMock()
    with patch("email_service.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__.return_value = smtp_instance
        result = email_service.send_email("cliente@teste.com", "Assunto", "Corpo")

    assert result is True
    smtp_instance.starttls.assert_called_once()
    smtp_instance.send_message.assert_called_once()
