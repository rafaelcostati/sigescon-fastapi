# app/repositories/usuario_repo.py
import asyncpg
from typing import Dict, Optional
from app.schemas.usuario_schema import UsuarioCreate

class UsuarioRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        # Retorna o usuário com a senha para verificação no login
        query = "SELECT * FROM usuario WHERE email = $1"
        user = await self.conn.fetchrow(query, email)
        return dict(user) if user else None

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        # Retorna o usuário sem a senha
        query = "SELECT id, nome, email, cpf, matricula, perfil_id, ativo FROM usuario WHERE id = $1 AND ativo = TRUE"
        user = await self.conn.fetchrow(query, user_id)
        return dict(user) if user else None

    async def create_user(self, user: UsuarioCreate, hashed_password: str) -> Dict:
        query = """
            INSERT INTO usuario (nome, email, cpf, matricula, senha, perfil_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, nome, email, cpf, matricula, perfil_id, ativo
        """
        new_user = await self.conn.fetchrow(
            query,
            user.nome, user.email, user.cpf,
            user.matricula, hashed_password, user.perfil_id
        )
        return dict(new_user)