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
        try:
            # Primeiro verifica se as tabelas existem
            check_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('contrato', 'contratados', 'usuario', 'status', 'relatoriofiscal', 'statusrelatorio')
            """
            existing_tables = await self.conn.fetch(check_query)
            table_names = [row['table_name'] for row in existing_tables]

            required_tables = ['contrato', 'contratados', 'usuario', 'status', 'relatoriofiscal', 'statusrelatorio']
            missing_tables = [table for table in required_tables if table not in table_names]

            if missing_tables:
                print(f"Tabelas não encontradas: {missing_tables}. Retornando lista vazia.")
                return []

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
            FROM contrato c
            JOIN contratados ct ON c.contratado_id = ct.id
            JOIN usuario u_gestor ON c.gestor_id = u_gestor.id
            JOIN usuario u_fiscal ON c.fiscal_id = u_fiscal.id
            JOIN status s ON c.status_id = s.id
            JOIN relatoriofiscal r ON r.contrato_id = c.id
            JOIN statusrelatorio sr ON r.status_relatorio_id = sr.id
            LEFT JOIN usuario u_ultimo_fiscal ON r.fiscal_usuario_id = u_ultimo_fiscal.id
            WHERE
                c.ativo = true
                AND sr.nome = 'Pendente de Análise'
            GROUP BY
                c.id, c.nr_contrato, c.objeto, c.data_inicio, c.data_fim,
                ct.nome, u_gestor.nome, u_fiscal.nome, s.nome, u_ultimo_fiscal.nome
            ORDER BY MAX(r.data_submissao) ASC
            LIMIT $1
            """
            rows = await self.conn.fetch(query, limit)
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"Erro ao buscar contratos com relatórios pendentes: {e}. Retornando lista vazia.")
            return []

    async def get_contratos_com_pendencias(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Busca contratos que têm pendências ativas (status 'Pendente')
        """
        try:
            # Primeiro verifica se as tabelas existem
            check_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('contrato', 'contratados', 'usuario', 'status', 'pendenciarelatorio', 'statuspendencia')
            """
            existing_tables = await self.conn.fetch(check_query)
            table_names = [row['table_name'] for row in existing_tables]

            required_tables = ['contrato', 'contratados', 'usuario', 'status', 'pendenciarelatorio', 'statuspendencia']
            missing_tables = [table for table in required_tables if table not in table_names]

            if missing_tables:
                print(f"Tabelas não encontradas: {missing_tables}. Retornando lista vazia.")
                return []

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
                SUM(CASE WHEN p.data_prazo < CURRENT_DATE THEN 1 ELSE 0 END) as pendencias_em_atraso,
                MAX(p.created_at) as ultima_pendencia_data
            FROM contrato c
            JOIN contratados ct ON c.contratado_id = ct.id
            JOIN usuario u_gestor ON c.gestor_id = u_gestor.id
            JOIN usuario u_fiscal ON c.fiscal_id = u_fiscal.id
            JOIN status s ON c.status_id = s.id
            JOIN pendenciarelatorio p ON p.contrato_id = c.id
            JOIN statuspendencia sp ON p.status_pendencia_id = sp.id
            WHERE
                c.ativo = true
                AND sp.nome = 'Pendente'
            GROUP BY
                c.id, c.nr_contrato, c.objeto, c.data_inicio, c.data_fim,
                ct.nome, u_gestor.nome, u_fiscal.nome, s.nome
            ORDER BY MAX(p.created_at) ASC
            LIMIT $1
            """
            rows = await self.conn.fetch(query, limit)
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"Erro ao buscar contratos com pendências: {e}. Retornando lista vazia.")
            return []

    async def get_minhas_pendencias_fiscal(self, fiscal_id: int) -> List[Dict[str, Any]]:
        """
        Busca todas as pendências ativas de um fiscal específico
        """
        try:
            # Primeiro verifica se as tabelas existem
            check_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('pendenciarelatorio', 'contrato', 'statuspendencia')
            """
            existing_tables = await self.conn.fetch(check_query)
            table_names = [row['table_name'] for row in existing_tables]

            required_tables = ['pendenciarelatorio', 'contrato', 'statuspendencia']
            missing_tables = [table for table in required_tables if table not in table_names]

            if missing_tables:
                print(f"Tabelas não encontradas: {missing_tables}. Retornando lista vazia.")
                return []

            query = """
            SELECT
                c.id as contrato_id,
                c.nr_contrato as contrato_numero,
                c.objeto as contrato_objeto,
                p.id as pendencia_id,
                p.descricao as pendencia_descricao,
                p.created_at,
                p.data_prazo,
                CASE
                    WHEN p.data_prazo IS NOT NULL AND p.data_prazo < CURRENT_DATE
                    THEN (CURRENT_DATE - p.data_prazo)::int
                    WHEN p.data_prazo IS NOT NULL
                    THEN (p.data_prazo - CURRENT_DATE)::int
                    ELSE NULL
                END as dias_restantes,
                CASE
                    WHEN p.data_prazo IS NOT NULL AND p.data_prazo < CURRENT_DATE
                    THEN true
                    ELSE false
                END as em_atraso
            FROM pendenciarelatorio p
            JOIN contrato c ON p.contrato_id = c.id
            JOIN statuspendencia sp ON p.status_pendencia_id = sp.id
            WHERE
                c.ativo = true
                AND c.fiscal_id = $1
                AND sp.nome = 'Pendente'
            ORDER BY
                CASE WHEN p.data_prazo < CURRENT_DATE THEN 0 ELSE 1 END,
                p.data_prazo ASC NULLS LAST,
                p.created_at ASC
            """
            rows = await self.conn.fetch(query, fiscal_id)
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"Erro ao buscar pendências do fiscal: {e}. Retornando lista vazia.")
            return []

    async def get_contadores_admin(self) -> Dict[str, int]:
        """
        Busca contadores para o dashboard do administrador
        """
        try:
            # Primeiro verifica se as tabelas existem
            check_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('relatoriofiscal', 'statusrelatorio', 'contrato', 'pendenciarelatorio', 'statuspendencia', 'usuario')
            """
            existing_tables = await self.conn.fetch(check_query)
            table_names = [row['table_name'] for row in existing_tables]

            contadores = {
                'relatorios_para_analise': 0,
                'contratos_com_pendencias': 0,
                'usuarios_ativos': 0,
                'contratos_ativos': 0,
                'minhas_pendencias': 0,
                'pendencias_em_atraso': 0,
                'relatorios_enviados_mes': 0,
                'contratos_sob_gestao': 0
            }

            # Relatórios para análise
            if all(table in table_names for table in ['relatoriofiscal', 'statusrelatorio']):
                query = """
                    SELECT COUNT(*)
                    FROM relatoriofiscal r
                    JOIN statusrelatorio sr ON r.status_relatorio_id = sr.id
                    WHERE sr.nome = 'Pendente de Análise'
                """
                result = await self.conn.fetchval(query)
                contadores['relatorios_para_analise'] = result or 0

            # Contratos com pendências
            if all(table in table_names for table in ['contrato', 'pendenciarelatorio', 'statuspendencia']):
                query = """
                    SELECT COUNT(DISTINCT c.id)
                    FROM contrato c
                    JOIN pendenciarelatorio p ON p.contrato_id = c.id
                    JOIN statuspendencia sp ON p.status_pendencia_id = sp.id
                    WHERE c.ativo = true AND sp.nome = 'Pendente'
                """
                result = await self.conn.fetchval(query)
                contadores['contratos_com_pendencias'] = result or 0

            # Usuários ativos
            if 'usuario' in table_names:
                query = """
                    SELECT COUNT(*)
                    FROM usuario
                    WHERE ativo = true
                """
                result = await self.conn.fetchval(query)
                contadores['usuarios_ativos'] = result or 0

            # Contratos ativos
            if 'contrato' in table_names:
                query = """
                    SELECT COUNT(*)
                    FROM contrato
                    WHERE ativo = true
                """
                result = await self.conn.fetchval(query)
                contadores['contratos_ativos'] = result or 0

            return contadores

        except Exception as e:
            print(f"Erro ao buscar contadores admin: {e}. Retornando contadores zerados.")
            return {
                'relatorios_para_analise': 0,
                'contratos_com_pendencias': 0,
                'usuarios_ativos': 0,
                'contratos_ativos': 0,
                'minhas_pendencias': 0,
                'pendencias_em_atraso': 0,
                'relatorios_enviados_mes': 0,
                'contratos_sob_gestao': 0
            }

    async def get_contadores_fiscal(self, fiscal_id: int) -> Dict[str, int]:
        """
        Busca contadores para o dashboard do fiscal
        """
        try:
            # Primeiro verifica se as tabelas existem
            check_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('pendenciarelatorio', 'contrato', 'statuspendencia', 'relatoriofiscal')
            """
            existing_tables = await self.conn.fetch(check_query)
            table_names = [row['table_name'] for row in existing_tables]

            contadores = {
                'minhas_pendencias': 0,
                'pendencias_em_atraso': 0,
                'relatorios_enviados_mes': 0
            }

            # Minhas pendências
            if all(table in table_names for table in ['pendenciarelatorio', 'contrato', 'statuspendencia']):
                query = """
                    SELECT COUNT(*)
                    FROM pendenciarelatorio p
                    JOIN contrato c ON p.contrato_id = c.id
                    JOIN statuspendencia sp ON p.status_pendencia_id = sp.id
                    WHERE c.fiscal_id = $1 AND c.ativo = true AND sp.nome = 'Pendente'
                """
                result = await self.conn.fetchval(query, fiscal_id)
                contadores['minhas_pendencias'] = result or 0

            # Pendências em atraso
            if all(table in table_names for table in ['pendenciarelatorio', 'contrato', 'statuspendencia']):
                query = """
                    SELECT COUNT(*)
                    FROM pendenciarelatorio p
                    JOIN contrato c ON p.contrato_id = c.id
                    JOIN statuspendencia sp ON p.status_pendencia_id = sp.id
                    WHERE c.fiscal_id = $1
                        AND c.ativo = true
                        AND sp.nome = 'Pendente'
                        AND p.data_prazo IS NOT NULL
                        AND p.data_prazo < CURRENT_DATE
                """
                result = await self.conn.fetchval(query, fiscal_id)
                contadores['pendencias_em_atraso'] = result or 0

            # Relatórios enviados no mês
            if all(table in table_names for table in ['relatoriofiscal', 'contrato']):
                query = """
                    SELECT COUNT(*)
                    FROM relatoriofiscal r
                    JOIN contrato c ON r.contrato_id = c.id
                    WHERE r.fiscal_usuario_id = $1
                        AND c.ativo = true
                        AND EXTRACT(MONTH FROM r.data_submissao) = EXTRACT(MONTH FROM CURRENT_DATE)
                        AND EXTRACT(YEAR FROM r.data_submissao) = EXTRACT(YEAR FROM CURRENT_DATE)
                """
                result = await self.conn.fetchval(query, fiscal_id)
                contadores['relatorios_enviados_mes'] = result or 0

            return contadores

        except Exception as e:
            print(f"Erro ao buscar contadores fiscal: {e}. Retornando contadores zerados.")
            return {
                'minhas_pendencias': 0,
                'pendencias_em_atraso': 0,
                'relatorios_enviados_mes': 0
            }

    async def get_pendencias_vencidas_admin(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca todas as pendências vencidas do sistema para o administrador
        com informações detalhadas e classificação de urgência
        """
        try:
            # Primeiro verifica se as tabelas existem
            check_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('pendenciarelatorio', 'contrato', 'usuario', 'statuspendencia')
            """
            existing_tables = await self.conn.fetch(check_query)
            table_names = [row['table_name'] for row in existing_tables]

            required_tables = ['pendenciarelatorio', 'contrato', 'usuario', 'statuspendencia']
            missing_tables = [table for table in required_tables if table not in table_names]

            if missing_tables:
                print(f"Tabelas não encontradas: {missing_tables}. Retornando lista vazia.")
                return []

            query = """
            SELECT
                p.id as pendencia_id,
                p.descricao,
                p.created_at,
                p.data_prazo,
                (CURRENT_DATE - p.data_prazo)::int as dias_em_atraso,

                -- Informações do contrato
                c.id as contrato_id,
                c.nr_contrato as contrato_numero,
                c.objeto as contrato_objeto,

                -- Responsáveis
                u_fiscal.nome as fiscal_nome,
                u_gestor.nome as gestor_nome,

                -- Classificação de urgência baseada nos dias em atraso
                CASE
                    WHEN (CURRENT_DATE - p.data_prazo) > 30 THEN 'CRÍTICA'
                    WHEN (CURRENT_DATE - p.data_prazo) BETWEEN 15 AND 30 THEN 'ALTA'
                    ELSE 'MÉDIA'
                END as urgencia

            FROM pendenciarelatorio p
            JOIN contrato c ON p.contrato_id = c.id
            JOIN usuario u_fiscal ON c.fiscal_id = u_fiscal.id
            JOIN usuario u_gestor ON c.gestor_id = u_gestor.id
            JOIN statuspendencia sp ON p.status_pendencia_id = sp.id
            WHERE
                c.ativo = true
                AND sp.nome = 'Pendente'
                AND p.data_prazo IS NOT NULL
                AND p.data_prazo < CURRENT_DATE
            ORDER BY
                -- Ordena por urgência (críticas primeiro) e depois por dias em atraso (maior primeiro)
                CASE
                    WHEN (CURRENT_DATE - p.data_prazo) > 30 THEN 1
                    WHEN (CURRENT_DATE - p.data_prazo) BETWEEN 15 AND 30 THEN 2
                    ELSE 3
                END,
                (CURRENT_DATE - p.data_prazo) DESC
            LIMIT $1
            """
            rows = await self.conn.fetch(query, limit)
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"Erro ao buscar pendências vencidas: {e}. Retornando lista vazia.")
            return []

    async def get_estatisticas_pendencias_vencidas(self) -> Dict[str, int]:
        """
        Busca estatísticas das pendências vencidas para o dashboard do administrador
        """
        try:
            # Primeiro verifica se as tabelas existem
            check_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('pendenciarelatorio', 'contrato', 'statuspendencia')
            """
            existing_tables = await self.conn.fetch(check_query)
            table_names = [row['table_name'] for row in existing_tables]

            required_tables = ['pendenciarelatorio', 'contrato', 'statuspendencia']
            missing_tables = [table for table in required_tables if table not in table_names]

            if missing_tables:
                print(f"Tabelas não encontradas: {missing_tables}. Retornando estatísticas zeradas.")
                return {
                    'total_pendencias_vencidas': 0,
                    'contratos_afetados': 0,
                    'pendencias_criticas': 0,
                    'pendencias_altas': 0,
                    'pendencias_medias': 0
                }

            query = """
            SELECT
                COUNT(*) as total_pendencias_vencidas,
                COUNT(DISTINCT c.id) as contratos_afetados,
                COALESCE(SUM(CASE WHEN (CURRENT_DATE - p.data_prazo) > 30 THEN 1 ELSE 0 END), 0) as pendencias_criticas,
                COALESCE(SUM(CASE WHEN (CURRENT_DATE - p.data_prazo) BETWEEN 15 AND 30 THEN 1 ELSE 0 END), 0) as pendencias_altas,
                COALESCE(SUM(CASE WHEN (CURRENT_DATE - p.data_prazo) BETWEEN 1 AND 14 THEN 1 ELSE 0 END), 0) as pendencias_medias
            FROM pendenciarelatorio p
            JOIN contrato c ON p.contrato_id = c.id
            JOIN statuspendencia sp ON p.status_pendencia_id = sp.id
            WHERE
                c.ativo = true
                AND sp.nome = 'Pendente'
                AND p.data_prazo IS NOT NULL
                AND p.data_prazo < CURRENT_DATE
            """
            result = await self.conn.fetchrow(query)
            return dict(result) if result else {
                'total_pendencias_vencidas': 0,
                'contratos_afetados': 0,
                'pendencias_criticas': 0,
                'pendencias_altas': 0,
                'pendencias_medias': 0
            }

        except Exception as e:
            print(f"Erro ao buscar estatísticas de pendências vencidas: {e}. Retornando estatísticas zeradas.")
            return {
                'total_pendencias_vencidas': 0,
                'contratos_afetados': 0,
                'pendencias_criticas': 0,
                'pendencias_altas': 0,
                'pendencias_medias': 0
            }

    async def get_contadores_gestor(self, gestor_id: int) -> Dict[str, int]:
        """
        Busca contadores para o dashboard do gestor
        """
        try:
            # Primeiro verifica se as tabelas existem
            check_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('contrato', 'relatoriofiscal', 'statusrelatorio')
            """
            existing_tables = await self.conn.fetch(check_query)
            table_names = [row['table_name'] for row in existing_tables]

            contadores = {
                'contratos_sob_gestao': 0,
                'relatorios_equipe_pendentes': 0
            }

            # Contratos sob gestão
            if 'contrato' in table_names:
                query = """
                    SELECT COUNT(*)
                    FROM contrato c
                    WHERE c.gestor_id = $1 AND c.ativo = true
                """
                result = await self.conn.fetchval(query, gestor_id)
                contadores['contratos_sob_gestao'] = result or 0

            # Relatórios da equipe pendentes
            if all(table in table_names for table in ['relatoriofiscal', 'contrato', 'statusrelatorio']):
                query = """
                    SELECT COUNT(*)
                    FROM relatoriofiscal r
                    JOIN contrato c ON r.contrato_id = c.id
                    JOIN statusrelatorio sr ON r.status_relatorio_id = sr.id
                    WHERE c.gestor_id = $1
                        AND c.ativo = true
                        AND sr.nome = 'Pendente de Análise'
                """
                result = await self.conn.fetchval(query, gestor_id)
                contadores['relatorios_equipe_pendentes'] = result or 0

            return contadores

        except Exception as e:
            print(f"Erro ao buscar contadores gestor: {e}. Retornando contadores zerados.")
            return {
                'contratos_sob_gestao': 0,
                'relatorios_equipe_pendentes': 0
            }

    async def get_pendencias_gestor(self, gestor_id: int) -> List[Dict[str, Any]]:
        """
        Busca todas as pendências dos contratos gerenciados pelo gestor
        """
        try:
            # Primeiro verifica se as tabelas existem
            check_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('pendenciarelatorio', 'contrato', 'statuspendencia', 'usuario')
            """
            existing_tables = await self.conn.fetch(check_query)
            table_names = [row['table_name'] for row in existing_tables]

            required_tables = ['pendenciarelatorio', 'contrato', 'statuspendencia', 'usuario']
            missing_tables = [table for table in required_tables if table not in table_names]

            if missing_tables:
                print(f"Tabelas não encontradas: {missing_tables}. Retornando lista vazia.")
                return []

            query = """
            SELECT
                p.id as pendencia_id,
                p.descricao,
                p.created_at,
                p.data_prazo,
                sp.nome as status_pendencia,

                -- Informações do contrato
                c.id as contrato_id,
                c.nr_contrato as contrato_numero,
                c.objeto as contrato_objeto,

                -- Fiscal responsável
                u_fiscal.nome as fiscal_nome,
                u_fiscal.email as fiscal_email,

                -- Status da pendência
                CASE
                    WHEN p.data_prazo IS NOT NULL AND p.data_prazo < CURRENT_DATE AND sp.nome = 'Pendente'
                    THEN 'vencida'
                    WHEN sp.nome = 'Pendente'
                    THEN 'pendente'
                    WHEN sp.nome = 'Concluída'
                    THEN 'concluida'
                    WHEN sp.nome = 'Cancelada'
                    THEN 'cancelada'
                    ELSE 'indefinido'
                END as status_classificacao,

                -- Dias restantes/vencidos
                CASE
                    WHEN p.data_prazo IS NOT NULL AND p.data_prazo < CURRENT_DATE
                    THEN (CURRENT_DATE - p.data_prazo)::int
                    WHEN p.data_prazo IS NOT NULL
                    THEN (p.data_prazo - CURRENT_DATE)::int
                    ELSE NULL
                END as dias_diferenca

            FROM pendenciarelatorio p
            JOIN contrato c ON p.contrato_id = c.id
            JOIN statuspendencia sp ON p.status_pendencia_id = sp.id
            JOIN usuario u_fiscal ON c.fiscal_id = u_fiscal.id
            WHERE
                c.gestor_id = $1
                AND c.ativo = true
            ORDER BY
                -- Ordena por: vencidas primeiro, depois por data de prazo
                CASE
                    WHEN p.data_prazo IS NOT NULL AND p.data_prazo < CURRENT_DATE AND sp.nome = 'Pendente' THEN 1
                    WHEN sp.nome = 'Pendente' THEN 2
                    WHEN sp.nome = 'Concluída' THEN 3
                    ELSE 4
                END,
                p.data_prazo ASC NULLS LAST,
                p.created_at DESC
            """
            rows = await self.conn.fetch(query, gestor_id)
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"Erro ao buscar pendências do gestor: {e}. Retornando lista vazia.")
            return []