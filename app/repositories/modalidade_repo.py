# app/repositories/modalidade_repo.py
import asyncpg
from typing import List, Optional, Dict

from app.schemas.modalidade_schema import ModalidadeUpdate

class ModalidadeRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_modalidade(self, nome: str) -> Dict:
        query = "INSERT INTO modalidade (nome) VALUES ($1) RETURNING *"
        new_modalidade = await self.conn.fetchrow(query, nome)
        return dict(new_modalidade)

    async def get_all_modalidades(self) -> List[Dict]:
        query = "SELECT * FROM modalidade WHERE ativo = TRUE ORDER BY nome"
        modalidades = await self.conn.fetch(query)
        return [dict(m) for m in modalidades]

    async def get_modalidade_by_id(self, modalidade_id: int) -> Optional[Dict]:
        query = "SELECT * FROM modalidade WHERE id = $1 AND ativo = TRUE"
        modalidade = await self.conn.fetchrow(query, modalidade_id)
        return dict(modalidade) if modalidade else None

    async def update_modalidade(self, modalidade_id: int, modalidade_update: ModalidadeUpdate) -> Optional[Dict]:
        update_data = modalidade_update.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_modalidade_by_id(modalidade_id)

        fields = ", ".join([f"{key} = ${i+2}" for i, key in enumerate(update_data.keys())])
        query = f"UPDATE modalidade SET {fields} WHERE id = $1 RETURNING *"
        
        updated_modalidade = await self.conn.fetchrow(query, modalidade_id, *update_data.values())
        return dict(updated_modalidade) if updated_modalidade else None

    async def delete_modalidade(self, modalidade_id: int) -> bool:
        query = "UPDATE modalidade SET ativo = FALSE WHERE id = $1 AND ativo = TRUE"
        status = await self.conn.execute(query, modalidade_id)
        return status.endswith('1')
        
    async def is_modalidade_in_use(self, modalidade_id: int) -> bool:
        """Verifica se a modalidade está sendo usada em algum contrato ativo."""
        query = "SELECT 1 FROM contrato WHERE modalidade_id = $1 AND ativo = TRUE LIMIT 1"
        in_use = await self.conn.fetchval(query, modalidade_id)
        return bool(in_use)