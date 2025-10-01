"""
Repository para logs de auditoria
"""
import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.schemas.audit_log_schema import AuditLogCreate, AuditLogFilter


class AuditLogRepository:
    """Repository para operações com logs de auditoria"""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_log(self, log_data: AuditLogCreate) -> Dict[str, Any]:
        """
        Cria um novo log de auditoria

        Args:
            log_data: Dados do log

        Returns:
            Log criado
        """
        query = """
            INSERT INTO audit_log (
                usuario_id, usuario_nome, perfil_usado,
                acao, entidade, entidade_id,
                descricao, dados_anteriores, dados_novos,
                ip_address, user_agent
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
        """

        row = await self.conn.fetchrow(
            query,
            log_data.usuario_id,
            log_data.usuario_nome,
            log_data.perfil_usado,
            log_data.acao,
            log_data.entidade,
            log_data.entidade_id,
            log_data.descricao,
            log_data.dados_anteriores,
            log_data.dados_novos,
            log_data.ip_address,
            log_data.user_agent
        )

        return dict(row) if row else None

    async def get_logs_with_filters(
        self,
        filters: AuditLogFilter
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Busca logs com filtros e paginação

        Args:
            filters: Filtros de busca

        Returns:
            Tupla (lista de logs, total de registros)
        """
        # Construir WHERE clause
        where_clauses = []
        params = []
        param_count = 1

        if filters.usuario_id:
            where_clauses.append(f"usuario_id = ${param_count}")
            params.append(filters.usuario_id)
            param_count += 1

        if filters.perfil:
            where_clauses.append(f"perfil_usado = ${param_count}")
            params.append(filters.perfil)
            param_count += 1

        if filters.acao:
            where_clauses.append(f"acao = ${param_count}")
            params.append(filters.acao)
            param_count += 1

        if filters.entidade:
            where_clauses.append(f"entidade = ${param_count}")
            params.append(filters.entidade)
            param_count += 1

        if filters.entidade_id:
            where_clauses.append(f"entidade_id = ${param_count}")
            params.append(filters.entidade_id)
            param_count += 1

        if filters.data_inicio:
            where_clauses.append(f"data_hora >= ${param_count}")
            params.append(filters.data_inicio)
            param_count += 1

        if filters.data_fim:
            # Adiciona 1 dia para incluir todo o dia final
            data_fim_inclusiva = filters.data_fim + timedelta(days=1)
            where_clauses.append(f"data_hora < ${param_count}")
            params.append(data_fim_inclusiva)
            param_count += 1

        if filters.busca:
            where_clauses.append(f"descricao ILIKE ${param_count}")
            params.append(f"%{filters.busca}%")
            param_count += 1

        # Construir query base
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Contar total
        count_query = f"SELECT COUNT(*) FROM audit_log WHERE {where_sql}"
        total = await self.conn.fetchval(count_query, *params)

        # Buscar logs paginados
        offset = (filters.pagina - 1) * filters.tamanho_pagina

        # Validar campo de ordenação
        valid_order_fields = ['id', 'data_hora', 'usuario_nome', 'acao', 'entidade']
        order_field = filters.ordenar_por if filters.ordenar_por in valid_order_fields else 'data_hora'
        order_dir = 'DESC' if filters.ordem.upper() == 'DESC' else 'ASC'

        data_query = f"""
            SELECT * FROM audit_log
            WHERE {where_sql}
            ORDER BY {order_field} {order_dir}
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([filters.tamanho_pagina, offset])

        rows = await self.conn.fetch(data_query, *params)
        logs = [dict(row) for row in rows]

        return logs, total

    async def get_log_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um log específico por ID

        Args:
            log_id: ID do log

        Returns:
            Log encontrado ou None
        """
        query = "SELECT * FROM audit_log WHERE id = $1"
        row = await self.conn.fetchrow(query, log_id)
        return dict(row) if row else None

    async def get_logs_by_entidade(
        self,
        entidade: str,
        entidade_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Busca logs de uma entidade específica

        Args:
            entidade: Tipo da entidade
            entidade_id: ID da entidade
            limit: Limite de resultados

        Returns:
            Lista de logs
        """
        query = """
            SELECT * FROM audit_log
            WHERE entidade = $1 AND entidade_id = $2
            ORDER BY data_hora DESC
            LIMIT $3
        """
        rows = await self.conn.fetch(query, entidade, entidade_id, limit)
        return [dict(row) for row in rows]

    async def get_logs_by_usuario(
        self,
        usuario_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Busca logs de um usuário específico

        Args:
            usuario_id: ID do usuário
            limit: Limite de resultados

        Returns:
            Lista de logs
        """
        query = """
            SELECT * FROM audit_log
            WHERE usuario_id = $1
            ORDER BY data_hora DESC
            LIMIT $2
        """
        rows = await self.conn.fetch(query, usuario_id, limit)
        return [dict(row) for row in rows]

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Gera estatísticas de auditoria

        Returns:
            Dicionário com estatísticas
        """
        # Total de logs
        total_logs = await self.conn.fetchval("SELECT COUNT(*) FROM audit_log")

        # Logs por ação
        logs_por_acao = await self.conn.fetch("""
            SELECT acao, COUNT(*) as count
            FROM audit_log
            GROUP BY acao
            ORDER BY count DESC
        """)

        # Logs por entidade
        logs_por_entidade = await self.conn.fetch("""
            SELECT entidade, COUNT(*) as count
            FROM audit_log
            GROUP BY entidade
            ORDER BY count DESC
        """)

        # Top 10 usuários mais ativos
        logs_por_usuario = await self.conn.fetch("""
            SELECT usuario_id, usuario_nome, COUNT(*) as count
            FROM audit_log
            GROUP BY usuario_id, usuario_nome
            ORDER BY count DESC
            LIMIT 10
        """)

        # Logs nas últimas 24 horas
        logs_ultimas_24h = await self.conn.fetchval("""
            SELECT COUNT(*)
            FROM audit_log
            WHERE data_hora >= NOW() - INTERVAL '24 hours'
        """)

        # Logs na última semana
        logs_ultima_semana = await self.conn.fetchval("""
            SELECT COUNT(*)
            FROM audit_log
            WHERE data_hora >= NOW() - INTERVAL '7 days'
        """)

        return {
            "total_logs": total_logs,
            "logs_por_acao": {row['acao']: row['count'] for row in logs_por_acao},
            "logs_por_entidade": {row['entidade']: row['count'] for row in logs_por_entidade},
            "logs_por_usuario": [
                {
                    "usuario_id": row['usuario_id'],
                    "usuario_nome": row['usuario_nome'],
                    "count": row['count']
                }
                for row in logs_por_usuario
            ],
            "logs_ultimas_24h": logs_ultimas_24h,
            "logs_ultima_semana": logs_ultima_semana
        }

    async def delete_old_logs(self, dias_retencao: int = 365) -> int:
        """
        Remove logs antigos

        Args:
            dias_retencao: Dias para manter os logs

        Returns:
            Número de registros deletados
        """
        query = """
            DELETE FROM audit_log
            WHERE data_hora < NOW() - ($1 || ' days')::INTERVAL
        """
        result = await self.conn.execute(query, dias_retencao)
        # Extrai o número de linhas afetadas do resultado
        count = int(result.split()[-1]) if result else 0
        return count
