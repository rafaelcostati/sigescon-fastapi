# app/repositories/contrato_repo.py
import asyncpg
from typing import List, Optional, Dict, Tuple

from app.schemas.contrato_schema import ContratoCreate, ContratoUpdate

class ContratoRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_contrato(self, contrato: ContratoCreate) -> Dict:
        contrato_data = contrato.model_dump()
        fields = ", ".join(contrato_data.keys())
        placeholders = ", ".join([f"${i+1}" for i in range(len(contrato_data))])
        
        query = f"""
            INSERT INTO contrato ({fields})
            VALUES ({placeholders})
            RETURNING id
        """
        new_contrato_id = await self.conn.fetchval(query, *contrato_data.values())
        return await self.find_contrato_by_id(new_contrato_id)


    # --- QUERY CORRIGIDA ---
    async def find_contrato_by_id(self, contrato_id: int) -> Optional[Dict]:
        query = """
            SELECT
                c.*,
                ct.nome AS contratado_nome,
                m.nome AS modalidade_nome,
                s.nome AS status_nome,
                gestor.nome AS gestor_nome,
                fiscal.nome AS fiscal_nome,
                fiscal_sub.nome AS fiscal_substituto_nome,
                doc.nome_arquivo AS documento_nome_arquivo 
            FROM contrato c
            LEFT JOIN contratado ct ON c.contratado_id = ct.id
            LEFT JOIN modalidade m ON c.modalidade_id = m.id
            LEFT JOIN status s ON c.status_id = s.id
            LEFT JOIN usuario gestor ON c.gestor_id = gestor.id
            LEFT JOIN usuario fiscal ON c.fiscal_id = fiscal.id
            LEFT JOIN usuario fiscal_sub ON c.fiscal_substituto_id = fiscal_sub.id
            LEFT JOIN arquivo doc ON c.documento = doc.id 
            WHERE c.id = $1 AND c.ativo = TRUE
        """
        contrato = await self.conn.fetchrow(query, contrato_id)
        return dict(contrato) if contrato else None


    async def get_all_contratos(
        self,
        filters: Optional[Dict] = None,
        order_by: str = 'c.data_fim DESC',
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        
        base_query = """
            FROM contrato c
            LEFT JOIN contratado ct ON c.contratado_id = ct.id
            LEFT JOIN modalidade m ON c.modalidade_id = m.id
            LEFT JOIN status s ON c.status_id = s.id
        """
        where_clauses = ["c.ativo = TRUE"]
        params = []
        param_idx = 1
        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                column_map = {'gestor_id': 'c.gestor_id', 'fiscal_id': 'c.fiscal_id', 'contratado_id': 'c.contratado_id', 'modalidade_id': 'c.modalidade_id', 'status_id': 'c.status_id', 'ano': 'EXTRACT(YEAR FROM c.data_inicio)'}
                if key in column_map:
                    where_clauses.append(f"{column_map[key]} = ${param_idx}")
                    params.append(value)
                    param_idx += 1
                elif key in ['objeto', 'nr_contrato', 'pae']:
                    where_clauses.append(f"c.{key} ILIKE ${param_idx}")
                    params.append(f"%{value}%")
                    param_idx += 1
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        count_query = f"SELECT COUNT(c.id) AS total {base_query}{where_sql}"
        total_items = await self.conn.fetchval(count_query, *params)
        data_query = f"""
            SELECT
                c.id, c.nr_contrato, c.objeto, c.data_fim,
                ct.nome as contratado_nome, 
                s.nome as status_nome
            {base_query}
            {where_sql}
            ORDER BY {order_by}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        paginated_params = params + [limit, offset]
        contratos = await self.conn.fetch(data_query, *paginated_params)
        return [dict(c) for c in contratos], total_items if total_items is not None else 0


    async def update_contrato(self, contrato_id: int, contrato: ContratoUpdate) -> Optional[Dict]:
        update_data = contrato.model_dump(exclude_unset=True)
        if not update_data:
            return await self.find_contrato_by_id(contrato_id)
        fields = ", ".join([f"{key} = ${i+2}" for i, key in enumerate(update_data.keys())])
        query = f"UPDATE contrato SET {fields}, updated_at = NOW() WHERE id = $1 RETURNING id"
        updated_id = await self.conn.fetchval(query, contrato_id, *update_data.values())
        if updated_id:
            return await self.find_contrato_by_id(updated_id)
        return None


    async def delete_contrato(self, contrato_id: int) -> bool:
        query = "UPDATE contrato SET ativo = FALSE, updated_at = NOW() WHERE id = $1 AND ativo = TRUE"
        status = await self.conn.execute(query, contrato_id)
        return status.endswith('1')