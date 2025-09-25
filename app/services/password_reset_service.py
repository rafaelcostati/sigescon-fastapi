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
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/reset-password?token={token}"

        subject = "🔒 Solicitação de Reset de Senha - SIGESCON"

        body = f"""
Olá {user['nome']},

Você solicitou a alteração de sua senha no Sistema de Gestão de Contratos (SIGESCON).

Para criar uma nova senha, clique no link abaixo:
{reset_url}

OU use o código diretamente no sistema:
{token}

⚠️ IMPORTANTE:
- Este link é válido por 24 horas
- Por segurança, use o link apenas uma vez
- Se você não solicitou esta alteração, ignore este email

Para sua segurança:
- Crie uma senha forte com pelo menos 6 caracteres
- Não compartilhe sua senha com ninguém
- Faça logout ao usar computadores compartilhados

Em caso de dúvidas, entre em contato com o administrador do sistema.

---
Sistema de Gestão de Contratos - SIGESCON
Este é um email automático, não responda.
        """

        return await EmailService.send_email(user['email'], subject, body)

    async def _send_password_changed_email(self, token_info: Dict[str, Any]) -> bool:
        """
        Envia email de confirmação após alteração de senha

        Args:
            token_info: Informações do token usado

        Returns:
            bool: True se email foi enviado
        """
        subject = "✅ Senha Alterada com Sucesso - SIGESCON"

        body = f"""
Olá {token_info['nome']},

Sua senha foi alterada com sucesso no Sistema de Gestão de Contratos (SIGESCON).

✅ Alteração realizada em: {token_info.get('used_at', 'agora')}
📧 Email da conta: {token_info['email']}

Se você não realizou esta alteração, entre em contato IMEDIATAMENTE com o administrador do sistema.

Para sua segurança:
- Faça login com sua nova senha
- Verifique se não há sessões ativas indevidas
- Mantenha suas credenciais sempre seguras

---
Sistema de Gestão de Contratos - SIGESCON
Este é um email automático, não responda.
        """

        return await EmailService.send_email(token_info['email'], subject, body)