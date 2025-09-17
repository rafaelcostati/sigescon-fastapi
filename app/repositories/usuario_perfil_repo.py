# app/repositories/usuario_perfil_repo.py - VERSÃO CORRIGIDA
import asyncpg
from typing import List, Dict, Optional

class UsuarioPerfilRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_user_profiles(self, usuario_id: int) -> List[Dict]:
        """Busca todos os perfis ativos de um usuário - CORRIGIDO"""
        query = """
            SELECT up.id, up.usuario_id, up.perfil_id, p.nome as perfil_nome,
                   up.data_concessao, up.observacoes, up.ativo
            FROM usuario_perfil up
            JOIN perfil p ON up.perfil_id = p.id
            WHERE up.usuario_id = $1 AND up.ativo = TRUE AND p.ativo = TRUE
            ORDER BY p.nome
        """
        records = await self.conn.fetch(query, usuario_id)
        
        # ✅ CORRIGIDO: Garante que o campo 'ativo' sempre seja incluído
        result = []
        for record in records:
            record_dict = dict(record)
            if 'ativo' not in record_dict:
                record_dict['ativo'] = True  # Valor padrão
            result.append(record_dict)
            
        return result

    async def has_profile(self, usuario_id: int, perfil_nome: str) -> bool:
        """Verifica se o usuário tem um perfil específico"""
        query = """
            SELECT 1 FROM usuario_perfil up
            JOIN perfil p ON up.perfil_id = p.id
            WHERE up.usuario_id = $1 AND p.nome = $2 
            AND up.ativo = TRUE AND p.ativo = TRUE
            LIMIT 1
        """
        result = await self.conn.fetchval(query, usuario_id, perfil_nome)
        return bool(result)

    async def has_any_profile(self, usuario_id: int, perfil_nomes: List[str]) -> bool:
        """Verifica se o usuário tem pelo menos um dos perfis especificados"""
        query = """
            SELECT 1 FROM usuario_perfil up
            JOIN perfil p ON up.perfil_id = p.id
            WHERE up.usuario_id = $1 AND p.nome = ANY($2::text[])
            AND up.ativo = TRUE AND p.ativo = TRUE
            LIMIT 1
        """
        result = await self.conn.fetchval(query, usuario_id, perfil_nomes)
        return bool(result)

    async def add_profile_to_user(self, usuario_id: int, perfil_id: int, 
                                 concedido_por: int, observacoes: Optional[str] = None) -> Dict:
        """Adiciona um perfil a um usuário - CORRIGIDO"""
        query = """
            INSERT INTO usuario_perfil (usuario_id, perfil_id, concedido_por_usuario_id, observacoes, ativo)
            VALUES ($1, $2, $3, $4, TRUE)
            ON CONFLICT (usuario_id, perfil_id) 
            DO UPDATE SET ativo = TRUE, data_concessao = NOW(), 
                         concedido_por_usuario_id = $3, observacoes = $4
            RETURNING id, usuario_id, perfil_id, ativo, data_concessao, observacoes
        """
        record = await self.conn.fetchrow(query, usuario_id, perfil_id, concedido_por, observacoes)
        
        # ✅ CORRIGIDO: Busca informações completas incluindo nome do perfil
        complete_query = """
            SELECT up.id, up.usuario_id, up.perfil_id, p.nome as perfil_nome,
                   up.data_concessao, up.observacoes, up.ativo
            FROM usuario_perfil up
            JOIN perfil p ON up.perfil_id = p.id
            WHERE up.id = $1
        """
        complete_record = await self.conn.fetchrow(complete_query, record['id'])
        return dict(complete_record)

    async def remove_profile_from_user(self, usuario_id: int, perfil_id: int) -> bool:
        """Remove um perfil de um usuário (soft delete)"""
        query = """
            UPDATE usuario_perfil 
            SET ativo = FALSE 
            WHERE usuario_id = $1 AND perfil_id = $2 AND ativo = TRUE
        """
        result = await self.conn.execute(query, usuario_id, perfil_id)
        return result.endswith('1')

    async def get_users_by_profile(self, perfil_nome: str, include_details: bool = False) -> List[Dict]:
        """Busca todos os usuários que têm um perfil específico"""
        if include_details:
            query = """
                SELECT DISTINCT u.id, u.nome, u.email, u.matricula
                FROM usuario u
                JOIN usuario_perfil up ON u.id = up.usuario_id
                JOIN perfil p ON up.perfil_id = p.id
                WHERE p.nome = $1 AND up.ativo = TRUE AND u.ativo = TRUE AND p.ativo = TRUE
                ORDER BY u.nome
            """
        else:
            query = """
                SELECT DISTINCT u.id, u.nome
                FROM usuario u
                JOIN usuario_perfil up ON u.id = up.usuario_id
                JOIN perfil p ON up.perfil_id = p.id
                WHERE p.nome = $1 AND up.ativo = TRUE AND u.ativo = TRUE AND p.ativo = TRUE
                ORDER BY u.nome
            """
        records = await self.conn.fetch(query, perfil_nome)
        return [dict(r) for r in records]

    async def get_user_complete_info(self, usuario_id: int) -> Optional[Dict]:
        """Busca informações completas do usuário incluindo todos os perfis"""
        query = """
            SELECT 
                u.*,
                array_agg(p.nome ORDER BY p.nome) FILTER (WHERE p.nome IS NOT NULL) as perfis,
                array_agg(p.id ORDER BY p.nome) FILTER (WHERE p.id IS NOT NULL) as perfil_ids
            FROM usuario u
            LEFT JOIN usuario_perfil up ON u.id = up.usuario_id AND up.ativo = TRUE
            LEFT JOIN perfil p ON up.perfil_id = p.id AND p.ativo = TRUE
            WHERE u.id = $1 AND u.ativo = TRUE
            GROUP BY u.id
        """
        record = await self.conn.fetchrow(query, usuario_id)
        return dict(record) if record else None

    async def validate_user_can_be_fiscal(self, usuario_id: int) -> bool:
        """Verifica se o usuário pode exercer função de fiscal"""
        return await self.has_any_profile(usuario_id, ["Administrador", "Fiscal"])

    async def validate_user_can_be_manager(self, usuario_id: int) -> bool:
        """Verifica se o usuário pode exercer função de gestor"""
        return await self.has_any_profile(usuario_id, ["Administrador", "Gestor"])

    async def get_available_fiscals(self) -> List[Dict]:
        """Busca todos os usuários que podem ser fiscais"""
        return await self.get_users_by_profile_list(["Administrador", "Fiscal"], include_details=True)

    async def get_available_managers(self) -> List[Dict]:
        """Busca todos os usuários que podem ser gestores"""
        return await self.get_users_by_profile_list(["Administrador", "Gestor"], include_details=True)

    async def get_users_by_profile_list(self, perfil_nomes: List[str], include_details: bool = False) -> List[Dict]:
        """Busca usuários que têm pelo menos um dos perfis especificados"""
        if include_details:
            query = """
                SELECT DISTINCT u.id, u.nome, u.email, u.matricula,
                       string_agg(DISTINCT p.nome, ', ' ORDER BY p.nome) as perfis_texto
                FROM usuario u
                JOIN usuario_perfil up ON u.id = up.usuario_id
                JOIN perfil p ON up.perfil_id = p.id
                WHERE p.nome = ANY($1::text[]) AND up.ativo = TRUE AND u.ativo = TRUE AND p.ativo = TRUE
                GROUP BY u.id, u.nome, u.email, u.matricula
                ORDER BY u.nome
            """
        else:
            query = """
                SELECT DISTINCT u.id, u.nome
                FROM usuario u
                JOIN usuario_perfil up ON u.id = up.usuario_id
                JOIN perfil p ON up.perfil_id = p.id
                WHERE p.nome = ANY($1::text[]) AND up.ativo = TRUE AND u.ativo = TRUE AND p.ativo = TRUE
                ORDER BY u.nome
            """
        records = await self.conn.fetch(query, perfil_nomes)
        return [dict(r) for r in records]

    async def get_profile_grant_history(self, usuario_id: int) -> List[Dict]:
        """Busca histórico de concessão/remoção de perfis"""
        query = """
            SELECT up.*, p.nome as perfil_nome, 
                   admin.nome as concedido_por_nome
            FROM usuario_perfil up
            JOIN perfil p ON up.perfil_id = p.id
            LEFT JOIN usuario admin ON up.concedido_por_usuario_id = admin.id
            WHERE up.usuario_id = $1
            ORDER BY up.data_concessao DESC
        """
        records = await self.conn.fetch(query, usuario_id)
        return [dict(r) for r in records]