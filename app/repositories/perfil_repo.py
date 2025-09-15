# app/repositories/perfil_repo.py
import asyncpg
from typing import Dict, Optional

class PerfilRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_perfil_by_id(self, perfil_id: int) -> Optional[Dict]:
        query = "SELECT * FROM perfil WHERE id = $1"
        perfil = await self.conn.fetchrow(query, perfil_id)
        return dict(perfil) if perfil else None