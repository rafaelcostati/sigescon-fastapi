# app/repositories/dashboard_repo.py
import asyncpg
from typing import List, Dict, Any
from datetime import date, datetime


class DashboardRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.conn = connection

    async def get_contratos_com_relatorios_pendentes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Busca contratos que têm relatórios aguardando análise pelo administrador
        """
        query = """
        SELECT DISTINCT
            c.id,
            c.nr_contrato,
            c.objeto,
            c.data_inicio,
            c.data_fim,
            ct.nome as contratado_nome,
            u_gestor.nome as gestor_nome,
            u_fiscal.nome as fiscal_nome,
            s.nome as status_nome,
            COUNT(r.id) as relatorios_pendentes_count,
            MAX(r.data_submissao) as ultimo_relatorio_data,
            u_ultimo_fiscal.nome as ultimo_relatorio_fiscal
        FROM contratos c
        JOIN contratados ct ON c.contratado_id = ct.id
        JOIN usuarios u_gestor ON c.gestor_id = u_gestor.id
        JOIN usuarios u_fiscal ON c.fiscal_id = u_fiscal.id
        JOIN status s ON c.status_id = s.id
        JOIN relatorios r ON r.contrato_id = c.id
        JOIN status_relatorio sr ON r.status_relatorio_id = sr.id
        LEFT JOIN usuarios u_ultimo_fiscal ON r.fiscal_usuario_id = u_ultimo_fiscal.id
        WHERE
            c.data_exclusao IS NULL
            AND sr.nome = 'Pendente de Análise'
        GROUP BY
            c.id, c.nr_contrato, c.objeto, c.data_inicio, c.data_fim,
            ct.nome, u_gestor.nome, u_fiscal.nome, s.nome, u_ultimo_fiscal.nome
        ORDER BY MAX(r.data_submissao) ASC
        LIMIT $1
        """
        rows = await self.conn.fetch(query, limit)
        return [dict(row) for row in rows]

    async def get_contratos_com_pendencias(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Busca contratos que têm pendências ativas (status 'Pendente')
        """
        query = """
        SELECT DISTINCT
            c.id,
            c.nr_contrato,
            c.objeto,
            c.data_inicio,
            c.data_fim,
            ct.nome as contratado_nome,
            u_gestor.nome as gestor_nome,
            u_fiscal.nome as fiscal_nome,
            s.nome as status_nome,
            COUNT(p.id) as pendencias_count,
            SUM(CASE WHEN p.prazo_entrega < CURRENT_DATE THEN 1 ELSE 0 END) as pendencias_em_atraso,
            MAX(p.data_criacao) as ultima_pendencia_data
        FROM contratos c
        JOIN contratados ct ON c.contratado_id = ct.id
        JOIN usuarios u_gestor ON c.gestor_id = u_gestor.id
        JOIN usuarios u_fiscal ON c.fiscal_id = u_fiscal.id
        JOIN status s ON c.status_id = s.id
        JOIN pendencias p ON p.contrato_id = c.id
        JOIN status_pendencia sp ON p.status_pendencia_id = sp.id
        WHERE
            c.data_exclusao IS NULL
            AND sp.nome = 'Pendente'
        GROUP BY
            c.id, c.nr_contrato, c.objeto, c.data_inicio, c.data_fim,
            ct.nome, u_gestor.nome, u_fiscal.nome, s.nome
        ORDER BY MAX(p.data_criacao) ASC
        LIMIT $1
        """
        rows = await self.conn.fetch(query, limit)
        return [dict(row) for row in rows]

    async def get_minhas_pendencias_fiscal(self, fiscal_id: int) -> List[Dict[str, Any]]:
        """
        Busca todas as pendências ativas de um fiscal específico
        """
        query = """
        SELECT
            c.id as contrato_id,
            c.nr_contrato as contrato_numero,
            c.objeto as contrato_objeto,
            p.id as pendencia_id,
            p.titulo as pendencia_titulo,
            p.descricao as pendencia_descricao,
            p.data_criacao,
            p.prazo_entrega,
            CASE
                WHEN p.prazo_entrega IS NOT NULL AND p.prazo_entrega < CURRENT_DATE
                THEN EXTRACT(DAY FROM CURRENT_DATE - p.prazo_entrega)::int
                WHEN p.prazo_entrega IS NOT NULL
                THEN EXTRACT(DAY FROM p.prazo_entrega - CURRENT_DATE)::int
                ELSE NULL
            END as dias_restantes,
            CASE
                WHEN p.prazo_entrega IS NOT NULL AND p.prazo_entrega < CURRENT_DATE
                THEN true
                ELSE false
            END as em_atraso
        FROM pendencias p
        JOIN contratos c ON p.contrato_id = c.id
        JOIN status_pendencia sp ON p.status_pendencia_id = sp.id
        WHERE
            c.data_exclusao IS NULL
            AND c.fiscal_id = $1
            AND sp.nome = 'Pendente'
        ORDER BY
            CASE WHEN p.prazo_entrega < CURRENT_DATE THEN 0 ELSE 1 END,
            p.prazo_entrega ASC NULLS LAST,
            p.data_criacao ASC
        """
        rows = await self.conn.fetch(query, fiscal_id)
        return [dict(row) for row in rows]

    async def get_contadores_admin(self) -> Dict[str, int]:
        """
        Busca contadores para o dashboard do administrador
        """
        queries = {
            'relatorios_para_analise': """
                SELECT COUNT(*)
                FROM relatorios r
                JOIN status_relatorio sr ON r.status_relatorio_id = sr.id
                WHERE sr.nome = 'Pendente de Análise'
            """,
            'contratos_com_pendencias': """
                SELECT COUNT(DISTINCT c.id)
                FROM contratos c
                JOIN pendencias p ON p.contrato_id = c.id
                JOIN status_pendencia sp ON p.status_pendencia_id = sp.id
                WHERE c.data_exclusao IS NULL AND sp.nome = 'Pendente'
            """,
            'usuarios_ativos': """
                SELECT COUNT(*)
                FROM usuarios
                WHERE data_exclusao IS NULL
            """,
            'contratos_ativos': """
                SELECT COUNT(*)
                FROM contratos
                WHERE data_exclusao IS NULL
            """
        }

        contadores = {}
        for nome, query in queries.items():
            result = await self.conn.fetchval(query)
            contadores[nome] = result

        return contadores

    async def get_contadores_fiscal(self, fiscal_id: int) -> Dict[str, int]:
        """
        Busca contadores para o dashboard do fiscal
        """
        queries = {
            'minhas_pendencias': """
                SELECT COUNT(*)
                FROM pendencias p
                JOIN contratos c ON p.contrato_id = c.id
                JOIN status_pendencia sp ON p.status_pendencia_id = sp.id
                WHERE c.fiscal_id = $1 AND c.data_exclusao IS NULL AND sp.nome = 'Pendente'
            """,
            'pendencias_em_atraso': """
                SELECT COUNT(*)
                FROM pendencias p
                JOIN contratos c ON p.contrato_id = c.id
                JOIN status_pendencia sp ON p.status_pendencia_id = sp.id
                WHERE c.fiscal_id = $1
                    AND c.data_exclusao IS NULL
                    AND sp.nome = 'Pendente'
                    AND p.prazo_entrega IS NOT NULL
                    AND p.prazo_entrega < CURRENT_DATE
            """,
            'relatorios_enviados_mes': """
                SELECT COUNT(*)
                FROM relatorios r
                JOIN contratos c ON r.contrato_id = c.id
                WHERE r.fiscal_usuario_id = $1
                    AND c.data_exclusao IS NULL
                    AND EXTRACT(MONTH FROM r.data_submissao) = EXTRACT(MONTH FROM CURRENT_DATE)
                    AND EXTRACT(YEAR FROM r.data_submissao) = EXTRACT(YEAR FROM CURRENT_DATE)
            """
        }

        contadores = {}
        for nome, query in queries.items():
            result = await self.conn.fetchval(query, fiscal_id)
            contadores[nome] = result

        return contadores

    async def get_contadores_gestor(self, gestor_id: int) -> Dict[str, int]:
        """
        Busca contadores para o dashboard do gestor
        """
        queries = {
            'contratos_sob_gestao': """
                SELECT COUNT(*)
                FROM contratos c
                WHERE c.gestor_id = $1 AND c.data_exclusao IS NULL
            """,
            'relatorios_equipe_pendentes': """
                SELECT COUNT(*)
                FROM relatorios r
                JOIN contratos c ON r.contrato_id = c.id
                JOIN status_relatorio sr ON r.status_relatorio_id = sr.id
                WHERE c.gestor_id = $1
                    AND c.data_exclusao IS NULL
                    AND sr.nome = 'Pendente de Análise'
            """
        }

        contadores = {}
        for nome, query in queries.items():
            result = await self.conn.fetchval(query, gestor_id)
            contadores[nome] = result

        return contadores