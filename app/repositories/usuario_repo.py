# app/repositories/usuario_repo.py
import asyncpg
from typing import Dict, Optional, List
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
            SELECT id, nome, email, cpf, matricula, perfil_id, ativo, created_at, updated_at 
            FROM usuario WHERE id = $1 AND ativo = TRUE
        """
        user = await self.conn.fetchrow(query, user_id)
        return dict(user) if user else None

    async def get_all_users(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Lista todos os usuários ativos com filtros opcionais"""
        query = """
            SELECT id, nome, email, cpf, matricula, perfil_id, ativo, created_at, updated_at 
            FROM usuario WHERE ativo = TRUE
        """
        params = []
        
        if filters and filters.get('nome'):
            query += " AND nome ILIKE $1"
            params.append(f"%{filters['nome']}%")
            
        query += " ORDER BY nome"
        
        if params:
            users = await self.conn.fetch(query, *params)
        else:
            users = await self.conn.fetch(query)
            
        return [dict(u) for u in users]

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
        
        # Monta a query dinamicamente
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

    async def update_user_password_hash(self, user_id: int, new_hash: str) -> bool:
        """Alias para compatibilidade - atualiza o hash da senha"""
        return await self.update_user_password(user_id, new_hash)

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