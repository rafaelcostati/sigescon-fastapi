# app/repositories/session_context_repo.py
import asyncpg
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import uuid

# Estado global compartilhado para persistir sessões entre instâncias
_GLOBAL_ACTIVE_PROFILES = {}

class SessionContextRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        # Estado temporário para simular sessões ativas - usar estado global compartilhado
        self._active_profiles = _GLOBAL_ACTIVE_PROFILES

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
        perfil_ativo_nome = next((p['nome'] for p in perfis_disponiveis if p['id'] == perfil_ativo_id), 'Gestor')

        session_data = {
            'id': 1,
            'usuario_id': usuario_id,
            'sessao_id': sessao_id,
            'perfil_ativo_id': perfil_ativo_id,
            'perfil_ativo_nome': perfil_ativo_nome,
            'perfis_disponiveis': json.dumps(perfis_disponiveis),
            'data_criacao': datetime.now(),
            'data_ultima_atividade': datetime.now(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'ativo': True
        }

        # Armazena na memória para futuras consultas
        self._active_profiles[sessao_id] = session_data

        return session_data

    async def get_session_context(self, sessao_id: str) -> Optional[Dict]:
        """Busca contexto de sessão com estado persistente simulado"""
        if sessao_id in self._active_profiles:
            context = self._active_profiles[sessao_id].copy()
        else:
            # Padrão para nova sessão
            context = {
                'sessao_id': sessao_id,
                'usuario_id': int(sessao_id.split('-')[-1]) if 'mock-session-' in sessao_id else 1,
                'perfil_ativo_id': 2,  # Gestor por padrão
                'perfil_ativo_nome': 'Gestor'
            }
            self._active_profiles[sessao_id] = context

        return context

    async def update_active_profile(self, sessao_id: str, novo_perfil_id: int, **kwargs) -> bool:
        """Atualiza perfil ativo com persistência simulada"""
        # Se a sessão não existe, cria uma nova entrada
        if sessao_id not in self._active_profiles:
            usuario_id = int(sessao_id.split('-')[-1]) if 'mock-session-' in sessao_id else 1
            self._active_profiles[sessao_id] = {
                'sessao_id': sessao_id,
                'usuario_id': usuario_id,
                'perfil_ativo_id': 2,  # Gestor por padrão
                'perfil_ativo_nome': 'Gestor'
            }

        # Busca nome do perfil
        nome_perfil = 'Gestor'
        if novo_perfil_id == 1:
            nome_perfil = 'Administrador'
        elif novo_perfil_id == 3:
            nome_perfil = 'Fiscal'

        self._active_profiles[sessao_id]['perfil_ativo_id'] = novo_perfil_id
        self._active_profiles[sessao_id]['perfil_ativo_nome'] = nome_perfil
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

    async def get_active_session_by_user(self, usuario_id: int) -> Optional[Dict]:
        """Busca sessão ativa do usuário com estado persistente"""
        sessao_id = f'mock-session-{usuario_id}'

        # Se já existe uma sessão salva, retorna ela
        if sessao_id in self._active_profiles:
            return self._active_profiles[sessao_id]

        # Senão cria uma nova sessão padrão
        session_data = {
            'sessao_id': sessao_id,
            'usuario_id': usuario_id,
            'perfil_ativo_id': 2,
            'perfil_ativo_nome': 'Gestor'
        }
        self._active_profiles[sessao_id] = session_data
        return session_data
