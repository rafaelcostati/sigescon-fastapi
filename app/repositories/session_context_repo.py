# app/repositories/session_context_repo.py 
import asyncpg
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import uuid

class SessionContextRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_user_available_profiles(self, usuario_id: int) -> List[Dict]:
        """Busca todos os perfis disponíveis para o usuário"""
        query = """
            SELECT p.id, p.nome, 
                   CASE 
                       WHEN p.nome = 'Administrador' THEN 'Acesso total ao sistema'
                       WHEN p.nome = 'Gestor' THEN 'Gestão de contratos e equipes'
                       WHEN p.nome = 'Fiscal' THEN 'Fiscalização e relatórios'
                       ELSE 'Perfil do sistema'
                   END as descricao
            FROM usuario_perfil up
            JOIN perfil p ON up.perfil_id = p.id
            WHERE up.usuario_id = $1 AND up.ativo = TRUE AND p.ativo = TRUE
            ORDER BY 
                CASE p.nome 
                    WHEN 'Administrador' THEN 1
                    WHEN 'Gestor' THEN 2
                    WHEN 'Fiscal' THEN 3
                    ELSE 4
                END
        """
        try:
            records = await self.conn.fetch(query, usuario_id)
            return [dict(r) for r in records]
        except Exception as e:
            print(f"Erro ao buscar perfis: {e}")
            return []

    async def validate_profile_for_user(self, usuario_id: int, perfil_id: int) -> bool:
        """Valida se o usuário pode usar um perfil específico"""
        query = """
            SELECT 1 FROM usuario_perfil up
            WHERE up.usuario_id = $1 AND up.perfil_id = $2 AND up.ativo = TRUE
        """
        try:
            result = await self.conn.fetchval(query, usuario_id, perfil_id)
            return bool(result)
        except Exception as e:
            print(f"Erro ao validar perfil: {e}")
            return False

    async def create_session_context(self, usuario_id: int, sessao_id: str, 
                                   perfil_ativo_id: int, perfis_disponiveis: List[Dict],
                                   ip_address: Optional[str] = None, 
                                   user_agent: Optional[str] = None) -> Dict:
        """Cria um contexto de sessão """
        return {
            'id': 1,
            'usuario_id': usuario_id,
            'sessao_id': sessao_id,
            'perfil_ativo_id': perfil_ativo_id,
            'perfis_disponiveis': json.dumps(perfis_disponiveis),
            'data_criacao': datetime.now(),
            'data_ultima_atividade': datetime.now(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'ativo': True
        }

    async def get_session_context(self, sessao_id: str) -> Optional[Dict]:
        """Busca contexto de sessão (mock)"""
        return {
            'sessao_id': sessao_id,
            'usuario_id': 1,
            'perfil_ativo_id': 1,
            'perfil_ativo_nome': 'Gestor'
        }

    async def update_active_profile(self, sessao_id: str, novo_perfil_id: int, **kwargs) -> bool:
        return True

    async def update_last_activity(self, sessao_id: str) -> bool:
        return True

    async def get_user_active_sessions(self, usuario_id: int) -> List[Dict]:
        return [{
            'sessao_id': f'mock-session-{usuario_id}',
            'usuario_id': usuario_id,
            'perfil_ativo_id': 2,
            'perfil_ativo_nome': 'Gestor',
            'data_ultima_atividade': datetime.now()
        }]

    async def deactivate_session(self, sessao_id: str) -> bool:
        return True

    async def cleanup_expired_sessions(self, hours: int = 24) -> int:
        return 0

    async def get_profile_switch_history(self, usuario_id: int, limit: int = 50) -> List[Dict]:
        return []
