# app/repositories/contratado_repo.py
import asyncpg
from typing import List, Optional, Dict, Any, Tuple
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

    
    async def delete_contratado(self, contratado_id: int) -> bool:
        query = "UPDATE contratado SET ativo = FALSE WHERE id = $1 AND ativo = TRUE"
        status = await self.conn.execute(query, contratado_id)
        # O execute retorna 'UPDATE 1' se uma linha foi afetada
        return status.endswith('1')
    
    async def get_all_contratados_paginated(
        self, 
        limit: int = 10, 
        offset: int = 0, 
        filters: Optional[Dict] = None
    ) -> Tuple[List[Dict], int]:
        """Busca contratados com paginação e filtros"""
        
        # Base da query
        where_clauses = ["ativo = TRUE"]
        params = []
        param_idx = 1
        
        # Aplica filtros se fornecidos
        if filters:
            for key, value in filters.items():
                if value is None or value == "":
                    continue
                    
                if key == 'nome':
                    where_clauses.append(f"nome ILIKE ${param_idx}")
                    params.append(f"%{value}%")
                    param_idx += 1
                elif key == 'cnpj':
                    where_clauses.append(f"cnpj = ${param_idx}")
                    params.append(value)
                    param_idx += 1
                elif key == 'cpf':
                    where_clauses.append(f"cpf = ${param_idx}")
                    params.append(value)
                    param_idx += 1
                elif key == 'email':
                    where_clauses.append(f"email ILIKE ${param_idx}")
                    params.append(f"%{value}%")
                    param_idx += 1
        
        where_sql = " WHERE " + " AND ".join(where_clauses)
        
        # Query para contar total de itens
        count_query = f"SELECT COUNT(*) FROM contratado{where_sql}"
        total_items = await self.conn.fetchval(count_query, *params)
        
        # Query para buscar dados paginados
        data_query = f"""
            SELECT * FROM contratado
            {where_sql}
            ORDER BY nome ASC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        
        # Adiciona limit e offset aos parâmetros
        paginated_params = params + [limit, offset]
        contratados = await self.conn.fetch(data_query, *paginated_params)
        
        return [dict(c) for c in contratados], total_items or 0