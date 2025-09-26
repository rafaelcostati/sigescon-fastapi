# app/services/password_reset_service.py

import asyncpg
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

from app.repositories.password_reset_repo import PasswordResetRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services.email_service import EmailService
from app.core.security import get_password_hash
from app.core.config import settings


class PasswordResetService:
    """Service para gerenciar o fluxo de reset de senha"""

    def __init__(self, connection: asyncpg.Connection):
        self.conn = connection
        self.reset_repo = PasswordResetRepository(connection)
        self.user_repo = UsuarioRepository(connection)

    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Processa solicitação de reset de senha

        Args:
            email: Email do usuário

        Returns:
            Dict com resultado da operação
        """
        # Busca usuário pelo email
        user = await self.user_repo.get_user_by_email(email)

        if not user:
            # Por segurança, não revelamos que o email não existe
            # Mas registramos a tentativa para auditoria
            print(f"⚠️ Tentativa de reset para email não cadastrado: {email}")
            return {
                "success": True,
                "message": "Solicitação enviada! Instruções para recuperar sua senha foram registradas."
            }

        if not user.get('ativo', True):
            # Usuário inativo também não deve receber reset
            print(f"⚠️ Tentativa de reset para usuário inativo: {email}")
            return {
                "success": True,
                "message": "Solicitação enviada! Instruções para recuperar sua senha foram registradas."
            }

        # Gera token de reset
        token = await self.reset_repo.create_reset_token(user['id'])

        # Envia email de reset
        email_sent = await self._send_reset_email(user, token)

        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno. Tente novamente mais tarde."
            )

        return {
            "success": True,
            "message": "Solicitação enviada! Instruções para recuperar sua senha foram registradas."
        }

    async def validate_reset_token(self, token: str) -> Dict[str, Any]:
        """
        Valida token de reset de senha

        Args:
            token: Token a ser validado

        Returns:
            Dict com resultado da validação
        """
        token_info = await self.reset_repo.validate_token(token)

        if not token_info:
            return {
                "valid": False,
                "message": "Token inválido, expirado ou já utilizado."
            }

        return {
            "valid": True,
            "message": "Token válido",
            "user_email": token_info['email']
        }

    async def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Efetua o reset da senha usando o token

        Args:
            token: Token de reset
            new_password: Nova senha

        Returns:
            Dict com resultado da operação
        """
        # Valida token
        token_info = await self.reset_repo.validate_token(token)

        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido, expirado ou já utilizado."
            )

        # Hash da nova senha
        password_hash = get_password_hash(new_password)

        # Atualiza senha do usuário
        success = await self.user_repo.update_user_password_hash(
            token_info['usuario_id'],
            password_hash
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao atualizar senha. Tente novamente."
            )

        # Marca token como usado
        await self.reset_repo.mark_token_as_used(token)

        # Envia email de confirmação
        await self._send_password_changed_email(token_info)

        return {
            "success": True,
            "message": "Senha alterada com sucesso!"
        }

    async def _send_reset_email(self, user: Dict[str, Any], token: str) -> bool:
        """
        Envia email com link para reset de senha

        Args:
            user: Dados do usuário
            token: Token de reset

        Returns:
            bool: True se email foi enviado
        """
        # Constrói URL de reset (assumindo que o frontend irá lidar com isso)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}" if hasattr(settings, 'FRONTEND_URL') else f"https://sigescon.pge.pa.gov.br/reset-password?token={token}"

        subject = "🔒 Solicitação de Reset de Senha - SIGESCON"

        # Email HTML com link clicável
        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset de Senha - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #495057;
        }}
        .reset-button {{
            display: inline-block;
            background-color: #007bff;
            color: white !important;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px 0;
            font-size: 16px;
            text-align: center;
        }}
        .reset-button:hover {{
            background-color: #0056b3;
        }}
        .button-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .warning-title {{
            font-weight: bold;
            color: #856404;
            margin-bottom: 10px;
        }}
        .warning-item {{
            margin: 8px 0;
            color: #856404;
        }}
        .security-tips {{
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .security-title {{
            font-weight: bold;
            color: #0c5460;
            margin-bottom: 10px;
        }}
        .security-item {{
            margin: 8px 0;
            color: #0c5460;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
        .url-fallback {{
            font-size: 12px;
            color: #6c757d;
            word-break: break-all;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🔒 SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="greeting">
            Olá <strong>{user['nome']}</strong>,
        </div>

        <p>Você solicitou a alteração de sua senha no Sistema de Gestão de Contratos (SIGESCON).</p>

        <div class="button-container">
            <a href="{reset_url}" class="reset-button">
                🔗 Criar Nova Senha
            </a>
        </div>

        <p class="url-fallback">
            Se o botão não funcionar, copie e cole este link no seu navegador:<br>
            <strong>{reset_url}</strong>
        </p>

        <div class="warning">
            <div class="warning-title">⚠️ IMPORTANTE:</div>
            <div class="warning-item">• Este link é válido por <strong>24 horas</strong></div>
            <div class="warning-item">• Por segurança, use o link apenas <strong>uma vez</strong></div>
            <div class="warning-item">• Se você não solicitou esta alteração, <strong>ignore este email</strong></div>
        </div>

        <div class="security-tips">
            <div class="security-title">🛡️ Para sua segurança:</div>
            <div class="security-item">• Crie uma senha forte com pelo menos 6 caracteres</div>
            <div class="security-item">• Não compartilhe sua senha com ninguém</div>
            <div class="security-item">• Faça logout ao usar computadores compartilhados</div>
        </div>

        <p>Em caso de dúvidas, entre em contato com o administrador do sistema.</p>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """

        return await EmailService.send_email(user['email'], subject, body, is_html=True)

    async def _send_password_changed_email(self, token_info: Dict[str, Any]) -> bool:
        """
        Envia email de confirmação após alteração de senha

        Args:
            token_info: Informações do token usado

        Returns:
            bool: True se email foi enviado
        """
        subject = "✅ Senha Alterada com Sucesso - SIGESCON"

        # Email HTML de confirmação
        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Senha Alterada - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .success-badge {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .success-title {{
            font-size: 20px;
            font-weight: bold;
            color: #155724;
            margin-bottom: 10px;
        }}
        .info-box {{
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .info-item {{
            margin: 8px 0;
            color: #0c5460;
        }}
        .alert-box {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .alert-text {{
            color: #721c24;
            font-weight: bold;
        }}
        .security-tips {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .security-title {{
            font-weight: bold;
            color: #856404;
            margin-bottom: 10px;
        }}
        .security-item {{
            margin: 8px 0;
            color: #856404;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">✅ SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="success-badge">
            <div class="success-title">🎉 Senha Alterada com Sucesso!</div>
            <p>Olá <strong>{token_info['nome']}</strong>, sua senha foi alterada com sucesso.</p>
        </div>

        <div class="info-box">
            <div class="info-item"><strong>⏰ Alteração realizada em:</strong> {token_info.get('used_at', 'agora')}</div>
            <div class="info-item"><strong>📧 Email da conta:</strong> {token_info['email']}</div>
        </div>

        <div class="alert-box">
            <div class="alert-text">
                🚨 Se você não realizou esta alteração, entre em contato IMEDIATAMENTE com o administrador do sistema.
            </div>
        </div>

        <div class="security-tips">
            <div class="security-title">🛡️ Para sua segurança:</div>
            <div class="security-item">• Faça login com sua nova senha</div>
            <div class="security-item">• Verifique se não há sessões ativas indevidas</div>
            <div class="security-item">• Mantenha suas credenciais sempre seguras</div>
        </div>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """

        return await EmailService.send_email(token_info['email'], subject, body, is_html=True)