# app/services/email_service.py
import aiosmtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_email(to_email: str, subject: str, body: str, test_mode: bool = False):
        """
        Envia email com logs detalhados e diferentes configurações SMTP

        Args:
            to_email: Email de destino
            subject: Assunto do email
            body: Corpo do email
            test_mode: Se True, tenta configurações alternativas em caso de falha
        """
        if not all([settings.SMTP_SERVER, settings.SENDER_EMAIL, settings.SENDER_PASSWORD]):
            logger.warning("AVISO: Variáveis de ambiente SMTP não configuradas. O e-mail não será enviado.")
            print("AVISO: Variáveis de ambiente SMTP não configuradas. O e-mail não será enviado.")
            return False

        message = MIMEMultipart()
        message["From"] = settings.SENDER_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Configurações para tentar em ordem de prioridade
        smtp_configs = [
            # Config 1: Padrão atual
            {
                "hostname": settings.SMTP_SERVER,
                "port": settings.SMTP_PORT or 587,
                "start_tls": True,
                "use_tls": False,
                "name": "STARTTLS (padrão)"
            },
            # Config 2: TLS direto na porta 465
            {
                "hostname": settings.SMTP_SERVER,
                "port": 465,
                "start_tls": False,
                "use_tls": True,
                "name": "TLS direto (465)"
            },
            # Config 3: Sem criptografia na porta 25
            {
                "hostname": settings.SMTP_SERVER,
                "port": 25,
                "start_tls": False,
                "use_tls": False,
                "name": "Sem TLS (25)"
            }
        ]

        last_error = None

        # Se não estiver em test_mode, tenta apenas a primeira configuração
        configs_to_try = smtp_configs if test_mode else [smtp_configs[0]]

        for config in configs_to_try:
            try:
                logger.info(f"Tentando enviar email para {to_email} usando {config['name']}")
                print(f"📧 Tentando enviar email para {to_email} usando {config['name']}")

                await aiosmtplib.send(
                    message,
                    hostname=config["hostname"],
                    port=config["port"],
                    username=settings.SENDER_EMAIL,
                    password=settings.SENDER_PASSWORD,
                    start_tls=config["start_tls"],
                    use_tls=config["use_tls"]
                )

                success_msg = f"✅ E-mail enviado com sucesso para {to_email} usando {config['name']}"
                logger.info(success_msg)
                print(success_msg)
                return True

            except Exception as e:
                error_msg = f"❌ Falha ao enviar e-mail para {to_email} usando {config['name']}: {e}"
                logger.error(error_msg)
                print(error_msg)
                last_error = e

                # Se não estiver em test_mode, para na primeira falha
                if not test_mode:
                    break

                # Se estiver em test_mode, continua tentando outras configurações
                continue

        # Se chegou aqui, todas as configurações falharam
        final_error = f"Falha ao enviar e-mail para {to_email}: {last_error}"
        logger.error(final_error)
        print(final_error)
        return False

    @staticmethod
    async def test_smtp_connection() -> dict:
        """
        Testa a conexão SMTP e retorna informações de diagnóstico
        """
        result = {
            "success": False,
            "config_working": None,
            "errors": [],
            "server_info": {
                "hostname": settings.SMTP_SERVER,
                "port": settings.SMTP_PORT,
                "username": settings.SENDER_EMAIL
            }
        }

        configs = [
            {"port": 587, "start_tls": True, "use_tls": False, "name": "STARTTLS (587)"},
            {"port": 465, "start_tls": False, "use_tls": True, "name": "TLS (465)"},
            {"port": 25, "start_tls": False, "use_tls": False, "name": "Plain (25)"}
        ]

        for config in configs:
            try:
                print(f"🔍 Testando {config['name']}...")

                # Teste de envio real
                test_result = await EmailService.send_email(
                    "test@example.com",  # Email que não existe para não spam
                    "Teste de Conexão SMTP",
                    "Este é um teste de conexão.",
                    test_mode=False
                )

                if test_result:
                    result["success"] = True
                    result["config_working"] = config
                    return result

            except Exception as e:
                result["errors"].append(f"{config['name']}: {str(e)}")

        return result