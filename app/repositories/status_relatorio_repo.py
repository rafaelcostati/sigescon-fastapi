# app/repositories/status_relatorio_repo.py
import asyncpg
from typing import List, Optional, Dict

class StatusRelatorioRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_all(self) -> List[Dict]:
        query = "SELECT * FROM statusrelatorio WHERE ativo = TRUE ORDER BY nome"
        records = await self.conn.fetch(query)
        return [dict(r) for r in records]

    async def get_by_id(self, status_id: int) -> Optional[Dict]:
        query = "SELECT * FROM statusrelatorio WHERE id = $1 AND ativo = TRUE"
        record = await self.conn.fetchrow(query, status_id)
        return dict(record) if record else None