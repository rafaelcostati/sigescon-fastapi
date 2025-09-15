# app/repositories/contratado_repo.py
import asyncpg
from typing import List, Optional, Dict, Any
from app.schemas.contratado_schema import ContratadoCreate, ContratadoUpdate

class ContratadoRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_contratado(self, contratado: ContratadoCreate) -> Dict:
        query = """
            INSERT INTO contratado (nome, email, cnpj, cpf, telefone)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """
        new_contratado = await self.conn.fetchrow(
            query,
            contratado.nome,
            contratado.email,
            contratado.cnpj,
            contratado.cpf,
            contratado.telefone,
        )
        return dict(new_contratado)

    async def get_contratado_by_id(self, contratado_id: int) -> Optional[Dict]:
        query = "SELECT * FROM contratado WHERE id = $1 AND ativo = TRUE"
        contratado = await self.conn.fetchrow(query, contratado_id)
        return dict(contratado) if contratado else None
        
    async def get_all_contratados(self) -> List[Dict]:
        query = "SELECT * FROM contratado WHERE ativo = TRUE ORDER BY nome"
        contratados = await self.conn.fetch(query)
        return [dict(c) for c in contratados]

    # --- NOVO MÉTODO DE ATUALIZAÇÃO ---
    async def update_contratado(self, contratado_id: int, contratado: ContratadoUpdate) -> Optional[Dict]:
        # Pega apenas os campos que foram enviados na requisição para não atualizar com None
        update_data = contratado.model_dump(exclude_unset=True)
        
        if not update_data:
            return await self.get_contratado_by_id(contratado_id)

        # Monta a query dinamicamente
        fields = ", ".join([f"{key} = ${i+2}" for i, key in enumerate(update_data.keys())])
        query = f"UPDATE contratado SET {fields} WHERE id = $1 RETURNING *"
        
        updated_contratado = await self.conn.fetchrow(query, contratado_id, *update_data.values())
        return dict(updated_contratado) if updated_contratado else None

    # --- NOVO MÉTODO DE EXCLUSÃO (SOFT DELETE) ---
    async def delete_contratado(self, contratado_id: int) -> bool:
        query = "UPDATE contratado SET ativo = FALSE WHERE id = $1 AND ativo = TRUE"
        status = await self.conn.execute(query, contratado_id)
        # O execute retorna 'UPDATE 1' se uma linha foi afetada
        return status.endswith('1')