# app/repositories/password_reset_repo.py

import asyncpg
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import secrets

class PasswordResetRepository:
    """Repository para gerenciar tokens de reset de senha"""

    def __init__(self, connection: asyncpg.Connection):
        self.conn = connection

    async def create_reset_token(self, usuario_id: int, expiration_hours: int = 24) -> str:
        """
        Cria um novo token de reset de senha para o usuário

        Args:
            usuario_id: ID do usuário
            expiration_hours: Horas até expiração (padrão: 24)

        Returns:
            str: Token gerado
        """
        # Gera token seguro
        token = secrets.token_urlsafe(32)

        # Calcula data de expiração
        expires_at = datetime.now() + timedelta(hours=expiration_hours)

        # Desativa tokens anteriores do mesmo usuário
        await self.conn.execute("""
            UPDATE password_reset_tokens
            SET used_at = CURRENT_TIMESTAMP
            WHERE usuario_id = $1 AND used_at IS NULL
        """, usuario_id)

        # Insere novo token
        await self.conn.execute("""
            INSERT INTO password_reset_tokens (token, usuario_id, expires_at)
            VALUES ($1, $2, $3)
        """, token, usuario_id, expires_at)

        return token

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Valida um token de reset de senha

        Args:
            token: Token a ser validado

        Returns:
            Dict com informações do token se válido, None caso contrário
        """
        query = """
            SELECT t.id, t.token, t.usuario_id, t.expires_at, t.used_at,
                   u.id as user_id, u.email, u.nome
            FROM password_reset_tokens t
            INNER JOIN usuario u ON t.usuario_id = u.id
            WHERE t.token = $1
              AND u.ativo = TRUE
        """

        result = await self.conn.fetchrow(query, token)

        if not result:
            return None

        # Verifica se token ainda não foi usado
        if result['used_at']:
            return None

        # Verifica se token não expirou
        if datetime.now() > result['expires_at']:
            return None

        return dict(result)

    async def mark_token_as_used(self, token: str) -> bool:
        """
        Marca um token como usado

        Args:
            token: Token a ser marcado

        Returns:
            bool: True se marcado com sucesso
        """
        result = await self.conn.execute("""
            UPDATE password_reset_tokens
            SET used_at = CURRENT_TIMESTAMP
            WHERE token = $1 AND used_at IS NULL
        """, token)

        # Verifica se alguma linha foi afetada
        return result.split()[-1] == "1"

    async def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações detalhadas de um token

        Args:
            token: Token a ser consultado

        Returns:
            Dict com informações completas do token
        """
        query = """
            SELECT t.*, u.email, u.nome
            FROM password_reset_tokens t
            INNER JOIN usuario u ON t.usuario_id = u.id
            WHERE t.token = $1
        """

        result = await self.conn.fetchrow(query, token)
        return dict(result) if result else None

    async def cleanup_expired_tokens(self) -> int:
        """
        Remove tokens expirados do banco de dados

        Returns:
            int: Número de tokens removidos
        """
        result = await self.conn.execute("""
            DELETE FROM password_reset_tokens
            WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
        """)

        # Extrai número de linhas afetadas
        return int(result.split()[-1])

    async def get_user_active_tokens(self, usuario_id: int) -> list:
        """
        Retorna todos os tokens ativos de um usuário

        Args:
            usuario_id: ID do usuário

        Returns:
            list: Lista de tokens ativos
        """
        query = """
            SELECT * FROM password_reset_tokens
            WHERE usuario_id = $1
              AND used_at IS NULL
              AND expires_at > CURRENT_TIMESTAMP
            ORDER BY created_at DESC
        """

        results = await self.conn.fetch(query, usuario_id)
        return [dict(row) for row in results]