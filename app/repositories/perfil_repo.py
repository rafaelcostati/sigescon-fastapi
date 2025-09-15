# app/repositories/perfil_repo.py
import asyncpg
from typing import List, Optional, Dict

class PerfilRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_perfil(self, nome: str) -> Dict:
        query = "INSERT INTO perfil (nome) VALUES ($1) RETURNING *"
        new_perfil = await self.conn.fetchrow(query, nome)
        return dict(new_perfil)

    async def get_all_perfis(self) -> List[Dict]:
        query = "SELECT * FROM perfil WHERE ativo = TRUE ORDER BY nome"
        perfis = await self.conn.fetch(query)
        return [dict(p) for p in perfis]

    async def get_perfil_by_id(self, perfil_id: int) -> Optional[Dict]:
        query = "SELECT * FROM perfil WHERE id = $1 AND ativo = TRUE"
        perfil = await self.conn.fetchrow(query, perfil_id)
        return dict(perfil) if perfil else None