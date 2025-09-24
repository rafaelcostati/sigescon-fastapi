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
            result = [dict(r) for r in records]
            print(f"🔍 DEBUG: Perfis encontrados para usuário {usuario_id}: {result}")
            return result
        except Exception as e:
            print(f"❌ Erro ao buscar perfis para usuário {usuario_id}: {e}")
            return []

    async def validate_profile_for_user(self, usuario_id: int, perfil_id: int) -> bool:
        """Valida se o usuário pode usar um perfil específico"""
        query = """
            SELECT 1 FROM usuario_perfil up
            WHERE up.usuario_id = $1 AND up.perfil_id = $2 AND up.ativo = TRUE
        """
        try:
            print(f"🔍 DEBUG: Validando perfil {perfil_id} para usuário {usuario_id}")
            result = await self.conn.fetchval(query, usuario_id, perfil_id)
            print(f"🔍 DEBUG: Resultado da validação: {bool(result)}")
            return bool(result)
        except Exception as e:
            print(f"❌ Erro ao validar perfil {perfil_id} para usuário {usuario_id}: {e}")
            return False

    async def create_session_context(self, usuario_id: int, sessao_id: str,
                                   perfil_ativo_id: int, perfis_disponiveis: List[Dict],
                                   ip_address: Optional[str] = None,
                                   user_agent: Optional[str] = None) -> Dict:
        """Cria um contexto de sessão na base de dados"""
        print(f"🔧 DEBUG: create_session_context - usuario {usuario_id}, sessao {sessao_id}, perfil {perfil_ativo_id}")

        perfil_ativo_nome = next((p['nome'] for p in perfis_disponiveis if p['id'] == perfil_ativo_id), 'Administrador')
        data_expiracao = datetime.now() + timedelta(days=30)  # Sessão expira em 30 dias

        # Primeiro, desativa sessões antigas do usuário
        await self.conn.execute("""
            UPDATE session_context
            SET ativo = FALSE
            WHERE usuario_id = $1 AND ativo = TRUE
        """, usuario_id)

        # Insere nova sessão no banco
        query = """
            INSERT INTO session_context (usuario_id, perfil_ativo_id, sessao_id, data_expiracao, ativo)
            VALUES ($1, $2, $3, $4, TRUE)
            RETURNING id, data_criacao
        """

        try:
            record = await self.conn.fetchrow(query, usuario_id, perfil_ativo_id, sessao_id, data_expiracao)
            print(f"✅ DEBUG: Sessão criada no banco - ID: {record['id']}")

            session_data = {
                'id': record['id'],
                'usuario_id': usuario_id,
                'sessao_id': sessao_id,
                'perfil_ativo_id': perfil_ativo_id,
                'perfil_ativo_nome': perfil_ativo_nome,
                'perfis_disponiveis': json.dumps(perfis_disponiveis),
                'data_criacao': record['data_criacao'],
                'data_ultima_atividade': datetime.now(),
                'ip_address': ip_address,
                'user_agent': user_agent,
                'ativo': True
            }

            return session_data

        except Exception as e:
            print(f"❌ ERROR: Erro ao criar sessão no banco: {e}")
            raise

    async def get_session_context(self, sessao_id: str) -> Optional[Dict]:
        """Busca contexto de sessão na base de dados"""
        print(f"🔍 DEBUG: get_session_context - buscando sessao {sessao_id}")

        # Buscar sessão ativa no banco
        query = """
            SELECT sc.id, sc.usuario_id, sc.perfil_ativo_id, sc.sessao_id,
                   sc.data_criacao, sc.data_expiracao,
                   p.nome as perfil_ativo_nome
            FROM session_context sc
            JOIN perfil p ON sc.perfil_ativo_id = p.id
            WHERE sc.sessao_id = $1 AND sc.ativo = TRUE
              AND (sc.data_expiracao IS NULL OR sc.data_expiracao > NOW())
        """

        try:
            record = await self.conn.fetchrow(query, sessao_id)

            if record:
                print(f"✅ DEBUG: Sessão encontrada no banco - usuario {record['usuario_id']}, perfil {record['perfil_ativo_nome']}")

                # Buscar perfis disponíveis para o usuário
                perfis_disponiveis = await self.get_user_available_profiles(record['usuario_id'])

                context = {
                    'id': record['id'],
                    'sessao_id': record['sessao_id'],
                    'usuario_id': record['usuario_id'],
                    'perfil_ativo_id': record['perfil_ativo_id'],
                    'perfil_ativo_nome': record['perfil_ativo_nome'],
                    'perfis_disponiveis': json.dumps(perfis_disponiveis),
                    'data_criacao': record['data_criacao'],
                    'data_ultima_atividade': datetime.now(),
                    'ativo': True
                }

                # Atualizar última atividade
                await self.update_last_activity(sessao_id)

                return context
            else:
                print(f"❌ DEBUG: Sessão {sessao_id} não encontrada ou expirada no banco")
                return None

        except Exception as e:
            print(f"❌ ERROR: Erro ao buscar sessão no banco: {e}")
            return None

    async def update_active_profile(self, sessao_id: str, novo_perfil_id: int, **kwargs) -> bool:
        """Atualiza perfil ativo na base de dados"""
        print(f"🔧 DEBUG: update_active_profile - sessao {sessao_id}, novo perfil {novo_perfil_id}")

        # Verificar se a sessão existe
        query_check = """
            SELECT id, usuario_id FROM session_context
            WHERE sessao_id = $1 AND ativo = TRUE
        """

        try:
            record = await self.conn.fetchrow(query_check, sessao_id)

            if not record:
                print(f"❌ ERROR: Sessão {sessao_id} não encontrada no banco")
                return False

            usuario_id = record['usuario_id']

            # Verificar se o usuário pode usar este perfil
            if not await self.validate_profile_for_user(usuario_id, novo_perfil_id):
                print(f"❌ ERROR: Usuário {usuario_id} não tem permissão para perfil {novo_perfil_id}")
                return False

            # Atualizar o perfil ativo na sessão
            query_update = """
                UPDATE session_context
                SET perfil_ativo_id = $1
                WHERE sessao_id = $2 AND ativo = TRUE
            """

            result = await self.conn.execute(query_update, novo_perfil_id, sessao_id)

            if result == "UPDATE 1":
                print(f"✅ DEBUG: Perfil atualizado no banco - sessao {sessao_id}, novo perfil {novo_perfil_id}")
                return True
            else:
                print(f"❌ ERROR: Falha ao atualizar perfil na sessão {sessao_id}")
                return False

        except Exception as e:
            print(f"❌ ERROR: Erro ao atualizar perfil no banco: {e}")
            return False

    async def update_last_activity(self, sessao_id: str) -> bool:
        """Atualiza última atividade da sessão - implementação simplificada"""
        # Removemos a atualização de última atividade por performance
        # A tabela não tem este campo ainda, implementaremos se necessário
        return True

    async def get_user_active_sessions(self, usuario_id: int) -> List[Dict]:
        """Busca todas as sessões ativas do usuário na base de dados"""
        query = """
            SELECT sc.id, sc.usuario_id, sc.perfil_ativo_id, sc.sessao_id,
                   sc.data_criacao, sc.data_expiracao,
                   p.nome as perfil_ativo_nome
            FROM session_context sc
            JOIN perfil p ON sc.perfil_ativo_id = p.id
            WHERE sc.usuario_id = $1 AND sc.ativo = TRUE
              AND (sc.data_expiracao IS NULL OR sc.data_expiracao > NOW())
            ORDER BY sc.data_criacao DESC
        """

        try:
            records = await self.conn.fetch(query, usuario_id)
            sessions = []

            for record in records:
                sessions.append({
                    'sessao_id': record['sessao_id'],
                    'usuario_id': record['usuario_id'],
                    'perfil_ativo_id': record['perfil_ativo_id'],
                    'perfil_ativo_nome': record['perfil_ativo_nome'],
                    'data_ultima_atividade': record['data_criacao']  # Usando data_criacao como última atividade
                })

            return sessions

        except Exception as e:
            print(f"❌ ERROR: Erro ao buscar sessões ativas: {e}")
            return []

    async def deactivate_session(self, sessao_id: str) -> bool:
        """Desativa uma sessão na base de dados"""
        query = """
            UPDATE session_context
            SET ativo = FALSE
            WHERE sessao_id = $1 AND ativo = TRUE
        """

        try:
            result = await self.conn.execute(query, sessao_id)
            return result == "UPDATE 1"
        except Exception as e:
            print(f"❌ ERROR: Erro ao desativar sessão: {e}")
            return False

    async def cleanup_expired_sessions(self, hours: int = 24) -> int:
        """Remove sessões expiradas da base de dados"""
        query = """
            UPDATE session_context
            SET ativo = FALSE
            WHERE ativo = TRUE
              AND data_expiracao IS NOT NULL
              AND data_expiracao < NOW()
        """

        try:
            result = await self.conn.execute(query)
            # Extrair número de linhas afetadas do resultado
            affected_rows = int(result.split()[-1]) if result.startswith("UPDATE") else 0
            print(f"🧹 DEBUG: Limpeza de sessões - {affected_rows} sessões expiradas removidas")
            return affected_rows
        except Exception as e:
            print(f"❌ ERROR: Erro na limpeza de sessões expiradas: {e}")
            return 0

    async def get_profile_switch_history(self, usuario_id: int, limit: int = 50) -> List[Dict]:
        return []

    async def get_active_session_by_user(self, usuario_id: int) -> Optional[Dict]:
        """Busca sessão ativa do usuário na base de dados"""
        print(f"🔍 DEBUG: get_active_session_by_user - usuario {usuario_id}")

        # Buscar sessão ativa mais recente do usuário
        query = """
            SELECT sc.id, sc.usuario_id, sc.perfil_ativo_id, sc.sessao_id,
                   sc.data_criacao, sc.data_expiracao,
                   p.nome as perfil_ativo_nome
            FROM session_context sc
            JOIN perfil p ON sc.perfil_ativo_id = p.id
            WHERE sc.usuario_id = $1 AND sc.ativo = TRUE
              AND (sc.data_expiracao IS NULL OR sc.data_expiracao > NOW())
            ORDER BY sc.data_criacao DESC
            LIMIT 1
        """

        try:
            record = await self.conn.fetchrow(query, usuario_id)

            if record:
                print(f"✅ DEBUG: Sessão ativa encontrada - sessao {record['sessao_id']}, perfil {record['perfil_ativo_nome']}")

                # Buscar perfis disponíveis para o usuário
                perfis_disponiveis = await self.get_user_available_profiles(usuario_id)

                session_data = {
                    'id': record['id'],
                    'sessao_id': record['sessao_id'],
                    'usuario_id': record['usuario_id'],
                    'perfil_ativo_id': record['perfil_ativo_id'],
                    'perfil_ativo_nome': record['perfil_ativo_nome'],
                    'perfis_disponiveis': json.dumps(perfis_disponiveis),
                    'data_criacao': record['data_criacao'],
                    'data_ultima_atividade': datetime.now(),
                    'ativo': True
                }

                return session_data
            else:
                print(f"❌ DEBUG: Nenhuma sessão ativa encontrada para usuário {usuario_id}")
                return None

        except Exception as e:
            print(f"❌ ERROR: Erro ao buscar sessão ativa: {e}")
            return None
