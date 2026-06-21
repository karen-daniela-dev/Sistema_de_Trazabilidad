"""
Servicio de email — activación de tutores y notificaciones.
En modo dev: imprime a consola. En producción: envía por SMTP.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config import settings

logger = logging.getLogger(__name__)


def _send_smtp(to: str, subject: str, html_body: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [to], msg.as_string())
        return True
    except Exception as exc:
        logger.error("Error enviando email a %s: %s", to, exc)
        return False


def send_activation_email(to_email: str, activation_token: str) -> bool:
    """
    Envía email de activación a un tutor recién registrado.
    El token permite al tutor establecer su contraseña.
    """
    link = f"{settings.API_BASE_URL}/auth/activate?token={activation_token}"
    subject = f"Activa tu cuenta — {settings.APP_NAME}"
    html = f"""
    <h2>Bienvenido a {settings.APP_NAME}</h2>
    <p>Tu cuenta como <strong>Tutor</strong> ha sido creada.</p>
    <p>Establece tu contraseña haciendo clic en el enlace (válido por 24 horas):</p>
    <a href="{link}" style="
        background:#1a56db;color:#fff;padding:10px 20px;
        border-radius:6px;text-decoration:none;font-weight:bold;
    ">Activar cuenta</a>
    <p style="margin-top:16px;color:#666;">Si no esperabas este email, puedes ignorarlo.</p>
    """

    if settings.DEBUG or not settings.SMTP_USER:
        logger.info("[DEV] Email de activación para %s: %s", to_email, link)
        print(f"\n[DEV EMAIL] Para: {to_email}\nEnlace: {link}\n")
        return True

    return _send_smtp(to_email, subject, html)
