# app/repositories/usuario_repo.py
import asyncpg
from typing import Dict, Optional, List, Tuple
from app.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate

class UsuarioRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Retorna o usuário com a senha para verificação no login"""
        query = "SELECT * FROM usuario WHERE email = $1 AND ativo = TRUE"
        user = await self.conn.fetchrow(query, email)
        return dict(user) if user else None

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Retorna o usuário sem a senha"""
        query = """
            SELECT u.id, u.nome, u.email, u.cpf, u.matricula, u.perfil_id, u.ativo, u.created_at, u.updated_at, p.nome as perfil_nome 
            FROM usuario u
            LEFT JOIN perfil p ON u.perfil_id = p.id
            WHERE u.id = $1 AND u.ativo = TRUE
        """
        user = await self.conn.fetchrow(query, user_id)
        return dict(user) if user else None

    async def get_all_users_paginated(
        self,
        filters: Optional[Dict] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Lista usuários ativos com filtros e paginação, retornando os dados e o total."""
        
        base_query = """
            FROM usuario u
            LEFT JOIN perfil p ON u.perfil_id = p.id
        """
        where_clauses = ["u.ativo = TRUE"]
        params = []
        param_idx = 1
        
        if filters and filters.get('nome'):
            where_clauses.append("u.nome ILIKE $1")
            params.append(f"%{filters['nome']}%")
            param_idx += 1
        
        where_sql = " WHERE " + " AND ".join(where_clauses)

        # Query para contar o total de itens
        count_query = f"SELECT COUNT(u.id) AS total {base_query}{where_sql}"
        total_items = await self.conn.fetchval(count_query, *params)
        
        # Query para buscar os dados paginados
        data_query = f"""
            SELECT u.id, u.nome, u.email, u.matricula, p.nome as perfil_nome
            {base_query}
            {where_sql}
            ORDER BY u.nome
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        paginated_params = params + [limit, offset]
        users = await self.conn.fetch(data_query, *paginated_params)
            
        return [dict(u) for u in users], total_items or 0

    async def create_user(self, user: UsuarioCreate, hashed_password: str) -> Dict:
        """Cria um novo usuário"""
        query = """
            INSERT INTO usuario (nome, email, cpf, matricula, senha, perfil_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, nome, email, cpf, matricula, perfil_id, ativo, created_at, updated_at
        """
        new_user = await self.conn.fetchrow(
            query,
            user.nome, user.email, user.cpf,
            user.matricula, hashed_password, user.perfil_id
        )
        return dict(new_user)

    async def update_user(self, user_id: int, user: UsuarioUpdate) -> Optional[Dict]:
        """Atualiza dados de um usuário"""
        update_data = user.model_dump(exclude_unset=True, exclude={'senha'})
        
        if not update_data:
            return await self.get_user_by_id(user_id)
        
        fields = ", ".join([f"{key} = ${i+2}" for i, key in enumerate(update_data.keys())])
        query = f"""
            UPDATE usuario SET {fields}, updated_at = NOW() 
            WHERE id = $1 AND ativo = TRUE
            RETURNING id, nome, email, cpf, matricula, perfil_id, ativo, created_at, updated_at
        """
        
        updated_user = await self.conn.fetchrow(query, user_id, *update_data.values())
        return dict(updated_user) if updated_user else None

    async def delete_user(self, user_id: int) -> bool:
        """Soft delete de um usuário"""
        query = "UPDATE usuario SET ativo = FALSE, updated_at = NOW() WHERE id = $1 AND ativo = TRUE"
        result = await self.conn.execute(query, user_id)
        return result.endswith('1')

    async def update_user_password(self, user_id: int, new_hash: str) -> bool:
        """Atualiza apenas a senha de um usuário"""
        query = "UPDATE usuario SET senha = $2, updated_at = NOW() WHERE id = $1 AND ativo = TRUE"
        result = await self.conn.execute(query, user_id, new_hash)
        return result.endswith('1')

    async def get_user_with_password(self, user_id: int) -> Optional[Dict]:
        """Retorna o usuário com a senha para verificação de senha antiga"""
        query = "SELECT id, senha FROM usuario WHERE id = $1 AND ativo = TRUE"
        user = await self.conn.fetchrow(query, user_id)
        return dict(user) if user else None

    async def check_email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica se um email já existe no banco"""
        if exclude_id:
            query = "SELECT 1 FROM usuario WHERE email = $1 AND id != $2 AND ativo = TRUE"
            exists = await self.conn.fetchval(query, email, exclude_id)
        else:
            query = "SELECT 1 FROM usuario WHERE email = $1 AND ativo = TRUE"
            exists = await self.conn.fetchval(query, email)
        return bool(exists)

    async def get_users_by_perfil(self, perfil_nome: str) -> List[Dict]:
        """Busca todos os usuários com um perfil específico"""
        query = """
            SELECT u.id, u.nome, u.email, u.cpf, u.matricula, u.perfil_id, u.ativo, u.created_at, u.updated_at, p.nome as perfil_nome
            FROM usuario u
            INNER JOIN perfil p ON u.perfil_id = p.id
            WHERE p.nome = $1 AND u.ativo = TRUE
            ORDER BY u.nome
        """
        records = await self.conn.fetch(query, perfil_nome)
        return [dict(r) for r in records]