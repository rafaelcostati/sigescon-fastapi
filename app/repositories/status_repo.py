# app/repositories/status_repo.py
import asyncpg
from typing import List, Optional, Dict

from app.schemas.status_schema import StatusUpdate

class StatusRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_status(self, nome: str) -> Dict:
        query = "INSERT INTO status (nome) VALUES ($1) RETURNING *"
        new_status = await self.conn.fetchrow(query, nome)
        return dict(new_status)

    async def get_all_status(self) -> List[Dict]:
        query = "SELECT * FROM status WHERE ativo = TRUE ORDER BY nome"
        all_status = await self.conn.fetch(query)
        return [dict(s) for s in all_status]

    async def get_status_by_id(self, status_id: int) -> Optional[Dict]:
        query = "SELECT * FROM status WHERE id = $1 AND ativo = TRUE"
        status = await self.conn.fetchrow(query, status_id)
        return dict(status) if status else None

    async def update_status(self, status_id: int, status_update: StatusUpdate) -> Optional[Dict]:
        update_data = status_update.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_status_by_id(status_id)

        fields = ", ".join([f"{key} = ${i+2}" for i, key in enumerate(update_data.keys())])
        query = f"UPDATE status SET {fields} WHERE id = $1 RETURNING *"
        
        updated_status = await self.conn.fetchrow(query, status_id, *update_data.values())
        return dict(updated_status) if updated_status else None

    async def delete_status(self, status_id: int) -> bool:
        query = "UPDATE status SET ativo = FALSE WHERE id = $1 AND ativo = TRUE"
        status = await self.conn.execute(query, status_id)
        return status.endswith('1')
        
    async def is_status_in_use(self, status_id: int) -> bool:
        """Verifica se o status está sendo usado em algum contrato ativo."""
        query = "SELECT 1 FROM contrato WHERE status_id = $1 AND ativo = TRUE LIMIT 1"
        in_use = await self.conn.fetchval(query, status_id)
        return bool(in_use)