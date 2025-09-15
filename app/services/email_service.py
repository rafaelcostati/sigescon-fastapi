# app/services/email_service.py
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings

class EmailService:
    @staticmethod
    async def send_email(to_email: str, subject: str, body: str):
        if not all([settings.SMTP_SERVER, settings.SENDER_EMAIL, settings.SENDER_PASSWORD]):
            print("AVISO: Variáveis de ambiente SMTP não configuradas. O e-mail não será enviado.")
            return

        message = MIMEMultipart()
        message["From"] = settings.SENDER_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_SERVER,
                port=settings.SMTP_PORT,
                username=settings.SENDER_EMAIL,
                password=settings.SENDER_PASSWORD,
                start_tls=True
            )
            print(f"E-mail enviado com sucesso para {to_email}")
        except Exception as e:
            print(f"Falha ao enviar e-mail para {to_email}: {e}")