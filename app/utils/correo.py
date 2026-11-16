"""Envío de correo por SMTP para la recuperación de contraseña (RF-14, HU-07).

Configuración por variables de entorno (se leen en cada envío, no al importar):
  MAIL_SERVER  servidor SMTP            (obligatoria)
  MAIL_USER    usuario de autenticación (obligatoria)
  MAIL_PASS    contraseña o app-password (obligatoria)
  MAIL_PORT    puerto, 587 por defecto (STARTTLS); 465 usa SSL directo
  MAIL_FROM    remitente, por defecto MAIL_USER
Si falta alguna de las tres obligatorias, ``smtp_configurado()`` es False y la
aplicación conserva el modo desarrollo (muestra el enlace en pantalla).
"""
import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger(__name__)


def smtp_configurado():
    return all(os.getenv(v) for v in ("MAIL_SERVER", "MAIL_USER", "MAIL_PASS"))


def enviar_enlace_recuperacion(destino, enlace, minutos=15):
    """Envía el enlace temporal. Devuelve True si el servidor SMTP lo aceptó."""
    if not smtp_configurado():
        return False
    msg = EmailMessage()
    msg["Subject"] = "Planeta Verde - Recuperación de contraseña"
    msg["From"] = os.getenv("MAIL_FROM") or os.environ["MAIL_USER"]
    msg["To"] = destino
    msg.set_content(
        "Hola,\n\nRecibimos una solicitud para restablecer tu contraseña en Planeta Verde.\n"
        f"Usa este enlace (vence en {minutos} minutos):\n\n{enlace}\n\n"
        "Si no fuiste tú, ignora este mensaje: tu contraseña no cambiará.\n"
    )
    servidor, puerto = os.environ["MAIL_SERVER"], int(os.getenv("MAIL_PORT", "587"))
    try:
        if puerto == 465:
            smtp = smtplib.SMTP_SSL(servidor, puerto, timeout=10)
        else:
            smtp = smtplib.SMTP(servidor, puerto, timeout=10)
        with smtp:
            if puerto != 465:
                smtp.starttls()
            smtp.login(os.environ["MAIL_USER"], os.environ["MAIL_PASS"])
            smtp.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError) as e:  # nunca se registra la contraseña
        log.error("No se pudo enviar el correo de recuperación: %s", e)
        return False
