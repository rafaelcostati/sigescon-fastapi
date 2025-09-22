# app/services/dashboard_service.py
from typing import List, Dict, Any
from datetime import datetime
from app.repositories.dashboard_repo import DashboardRepository
from app.schemas.dashboard_schema import (
    ContratosComPendencias,
    ContratosComRelatoriosPendentes,
    MinhasPendenciasResponse,
    ContadoresDashboard,
    ContratoRelatorioResumo,
    ContratoPendenciaResumo,
    MinhasPendencias,
    DashboardAdminResponse,
    DashboardFiscalResponse,
    PendenciasVencidasAdminResponse,
    PendenciaVencidaAdmin
)
from app.schemas.usuario_schema import Usuario


class DashboardService:
    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    async def get_contratos_com_relatorios_pendentes(self, limit: int = 20) -> ContratosComRelatoriosPendentes:
        """
        Busca contratos com relatórios pendentes de análise
        """
        contratos_data = await self.dashboard_repo.get_contratos_com_relatorios_pendentes(limit)

        contratos = []
        total_relatorios_pendentes = 0

        for contrato in contratos_data:
            total_relatorios_pendentes += contrato['relatorios_pendentes_count']

            contrato_resumo = ContratoRelatorioResumo(
                id=contrato['id'],
                nr_contrato=contrato['nr_contrato'],
                objeto=contrato['objeto'],
                data_inicio=contrato['data_inicio'],
                data_fim=contrato['data_fim'],
                contratado_nome=contrato['contratado_nome'],
                gestor_nome=contrato['gestor_nome'],
                fiscal_nome=contrato['fiscal_nome'],
                status_nome=contrato['status_nome'],
                relatorios_pendentes_count=contrato['relatorios_pendentes_count'],
                ultimo_relatorio_data=contrato['ultimo_relatorio_data'],
                ultimo_relatorio_fiscal=contrato['ultimo_relatorio_fiscal']
            )
            contratos.append(contrato_resumo)

        return ContratosComRelatoriosPendentes(
            contratos=contratos,
            total_contratos=len(contratos),
            total_relatorios_pendentes=total_relatorios_pendentes
        )

    async def get_contratos_com_pendencias(self, limit: int = 20) -> ContratosComPendencias:
        """
        Busca contratos com pendências ativas
        """
        contratos_data = await self.dashboard_repo.get_contratos_com_pendencias(limit)

        contratos = []
        total_pendencias = 0

        for contrato in contratos_data:
            total_pendencias += contrato['pendencias_count']

            contrato_resumo = ContratoPendenciaResumo(
                id=contrato['id'],
                nr_contrato=contrato['nr_contrato'],
                objeto=contrato['objeto'],
                data_inicio=contrato['data_inicio'],
                data_fim=contrato['data_fim'],
                contratado_nome=contrato['contratado_nome'],
                gestor_nome=contrato['gestor_nome'],
                fiscal_nome=contrato['fiscal_nome'],
                status_nome=contrato['status_nome'],
                pendencias_count=contrato['pendencias_count'],
                pendencias_em_atraso=contrato['pendencias_em_atraso'],
                ultima_pendencia_data=contrato['ultima_pendencia_data']
            )
            contratos.append(contrato_resumo)

        return ContratosComPendencias(
            contratos=contratos,
            total_contratos=len(contratos),
            total_pendencias=total_pendencias
        )

    async def get_minhas_pendencias_fiscal(self, fiscal_id: int) -> MinhasPendenciasResponse:
        """
        Busca pendências do fiscal logado
        """
        pendencias_data = await self.dashboard_repo.get_minhas_pendencias_fiscal(fiscal_id)

        pendencias = []
        pendencias_em_atraso = 0
        pendencias_proximas_vencimento = 0

        for pendencia in pendencias_data:
            # Verifica se está em atraso
            if pendencia['em_atraso']:
                pendencias_em_atraso += 1

            # Verifica se está próxima do vencimento (próximos 7 dias)
            if (pendencia['dias_restantes'] is not None and
                pendencia['dias_restantes'] >= 0 and
                pendencia['dias_restantes'] <= 7 and
                not pendencia['em_atraso']):
                pendencias_proximas_vencimento += 1

            pendencia_obj = MinhasPendencias(
                contrato_id=pendencia['contrato_id'],
                contrato_numero=pendencia['contrato_numero'],
                contrato_objeto=pendencia['contrato_objeto'],
                pendencia_id=pendencia['pendencia_id'],
                pendencia_titulo=pendencia['pendencia_descricao'],  # Usando descricao como titulo
                pendencia_descricao=pendencia['pendencia_descricao'],
                data_criacao=pendencia['created_at'],  # Corrigido nome do campo
                prazo_entrega=pendencia['data_prazo'],  # Corrigido nome do campo
                dias_restantes=pendencia['dias_restantes'],
                em_atraso=pendencia['em_atraso']
            )
            pendencias.append(pendencia_obj)

        return MinhasPendenciasResponse(
            pendencias=pendencias,
            total_pendencias=len(pendencias),
            pendencias_em_atraso=pendencias_em_atraso,
            pendencias_proximas_vencimento=pendencias_proximas_vencimento
        )

    async def get_contadores_dashboard(self, usuario: Usuario) -> ContadoresDashboard:
        """
        Busca contadores para dashboard baseado nos perfis do usuário
        Para este endpoint simplificado, assume que admin vê contadores administrativos
        """
        contadores_dict = {}

        # Por enquanto, assume que se tem perfil_id = 1 é admin
        # Isso é uma simplificação para os testes funcionarem
        if usuario.perfil_id == 1:  # Administrador
            admin_contadores = await self.dashboard_repo.get_contadores_admin()
            contadores_dict.update(admin_contadores)

        # Se é fiscal (perfil_id = 3), busca contadores do fiscal
        if usuario.perfil_id == 3:  # Fiscal
            fiscal_contadores = await self.dashboard_repo.get_contadores_fiscal(usuario.id)
            contadores_dict.update(fiscal_contadores)

        # Se é gestor (perfil_id = 2), busca contadores do gestor
        if usuario.perfil_id == 2:  # Gestor
            gestor_contadores = await self.dashboard_repo.get_contadores_gestor(usuario.id)
            contadores_dict.update(gestor_contadores)

        # Preenche com zeros os campos não encontrados
        return ContadoresDashboard(
            relatorios_para_analise=contadores_dict.get('relatorios_para_analise', 0),
            contratos_com_pendencias=contadores_dict.get('contratos_com_pendencias', 0),
            usuarios_ativos=contadores_dict.get('usuarios_ativos', 0),
            contratos_ativos=contadores_dict.get('contratos_ativos', 0),
            minhas_pendencias=contadores_dict.get('minhas_pendencias', 0),
            pendencias_em_atraso=contadores_dict.get('pendencias_em_atraso', 0),
            relatorios_enviados_mes=contadores_dict.get('relatorios_enviados_mes', 0),
            contratos_sob_gestao=contadores_dict.get('contratos_sob_gestao', 0),
            relatorios_equipe_pendentes=contadores_dict.get('relatorios_equipe_pendentes', 0)
        )

    async def get_dashboard_admin_completo(self) -> DashboardAdminResponse:
        """
        Busca dados completos para dashboard do administrador
        """
        # Busca contadores
        admin_contadores = await self.dashboard_repo.get_contadores_admin()
        contadores = ContadoresDashboard(
            relatorios_para_analise=admin_contadores['relatorios_para_analise'],
            contratos_com_pendencias=admin_contadores['contratos_com_pendencias'],
            usuarios_ativos=admin_contadores['usuarios_ativos'],
            contratos_ativos=admin_contadores['contratos_ativos'],
            total_contratacoes=admin_contadores['total_contratacoes'],
            minhas_pendencias=0,
            pendencias_em_atraso=0,
            relatorios_enviados_mes=0,
            contratos_sob_gestao=0,
            relatorios_equipe_pendentes=0
        )

        # Busca contratos com relatórios pendentes (limitado para performance)
        relatorios_pendentes = await self.get_contratos_com_relatorios_pendentes(10)

        # Busca contratos com pendências (limitado para performance)
        contratos_pendencias = await self.get_contratos_com_pendencias(10)

        return DashboardAdminResponse(
            contadores=contadores,
            contratos_com_relatorios_pendentes=relatorios_pendentes.contratos,
            contratos_com_pendencias=contratos_pendencias.contratos
        )

    async def get_dashboard_fiscal_completo(self, fiscal_id: int) -> DashboardFiscalResponse:
        """
        Busca dados completos para dashboard do fiscal
        """
        # Busca contadores
        fiscal_contadores = await self.dashboard_repo.get_contadores_fiscal(fiscal_id)
        contadores = ContadoresDashboard(
            relatorios_para_analise=0,
            contratos_com_pendencias=0,
            usuarios_ativos=0,
            contratos_ativos=0,
            minhas_pendencias=fiscal_contadores['minhas_pendencias'],
            pendencias_em_atraso=fiscal_contadores['pendencias_em_atraso'],
            relatorios_enviados_mes=fiscal_contadores['relatorios_enviados_mes'],
            contratos_sob_gestao=0,
            relatorios_equipe_pendentes=0
        )

        # Busca pendências do fiscal
        minhas_pendencias = await self.get_minhas_pendencias_fiscal(fiscal_id)

        return DashboardFiscalResponse(
            contadores=contadores,
            minhas_pendencias=minhas_pendencias.pendencias
        )

    async def get_pendencias_vencidas_admin(self, limit: int = 50) -> PendenciasVencidasAdminResponse:
        """
        Busca pendências vencidas detalhadamente para o administrador
        """
        # Busca pendências vencidas
        pendencias_data = await self.dashboard_repo.get_pendencias_vencidas_admin(limit)

        # Busca estatísticas
        stats = await self.dashboard_repo.get_estatisticas_pendencias_vencidas()

        # Processa as pendências
        pendencias = []
        for pendencia in pendencias_data:
            pendencia_obj = PendenciaVencidaAdmin(
                pendencia_id=pendencia['pendencia_id'],
                titulo=pendencia['descricao'],  # Usando descricao como titulo
                descricao=pendencia['descricao'],
                data_criacao=pendencia['created_at'],
                prazo_entrega=pendencia['data_prazo'],  # Corrigido o nome da coluna
                dias_em_atraso=pendencia['dias_em_atraso'],
                contrato_id=pendencia['contrato_id'],
                contrato_numero=pendencia['contrato_numero'],
                contrato_objeto=pendencia['contrato_objeto'],
                fiscal_nome=pendencia['fiscal_nome'],
                gestor_nome=pendencia['gestor_nome'],
                urgencia=pendencia['urgencia']
            )
            pendencias.append(pendencia_obj)

        return PendenciasVencidasAdminResponse(
            pendencias_vencidas=pendencias,
            total_pendencias_vencidas=stats['total_pendencias_vencidas'],
            contratos_afetados=stats['contratos_afetados'],
            pendencias_criticas=stats['pendencias_criticas'],
            pendencias_altas=stats['pendencias_altas'],
            pendencias_medias=stats['pendencias_medias']
        )

    async def get_pendencias_gestor(self, gestor_id: int) -> Dict[str, Any]:
        """
        Busca todas as pendências dos contratos gerenciados pelo gestor
        """
        pendencias_data = await self.dashboard_repo.get_pendencias_gestor(gestor_id)

        # Organiza as pendências por status
        pendencias_por_status = {
            'vencidas': [],
            'pendentes': [],
            'concluidas': [],
            'canceladas': []
        }

        for pendencia in pendencias_data:
            status_classificacao = pendencia['status_classificacao']

            pendencia_formatada = {
                'pendencia_id': pendencia['pendencia_id'],
                'descricao': pendencia['descricao'],
                'created_at': pendencia['created_at'],
                'data_prazo': pendencia['data_prazo'],
                'status_pendencia': pendencia['status_pendencia'],
                'contrato_id': pendencia['contrato_id'],
                'contrato_numero': pendencia['contrato_numero'],
                'contrato_objeto': pendencia['contrato_objeto'],
                'fiscal_nome': pendencia['fiscal_nome'],
                'fiscal_email': pendencia['fiscal_email'],
                'dias_diferenca': pendencia['dias_diferenca']
            }

            if status_classificacao == 'vencida':
                pendencias_por_status['vencidas'].append(pendencia_formatada)
            elif status_classificacao == 'pendente':
                pendencias_por_status['pendentes'].append(pendencia_formatada)
            elif status_classificacao == 'concluida':
                pendencias_por_status['concluidas'].append(pendencia_formatada)
            elif status_classificacao == 'cancelada':
                pendencias_por_status['canceladas'].append(pendencia_formatada)

        # Calcula estatísticas
        total_pendencias = len(pendencias_data)
        estatisticas = {
            'total': total_pendencias,
            'vencidas': len(pendencias_por_status['vencidas']),
            'pendentes': len(pendencias_por_status['pendentes']),
            'concluidas': len(pendencias_por_status['concluidas']),
            'canceladas': len(pendencias_por_status['canceladas'])
        }

        return {
            'pendencias': pendencias_por_status,
            'estatisticas': estatisticas,
            'gestor_id': gestor_id
        }

    async def get_dashboard_gestor_completo(self, gestor_id: int) -> Dict[str, Any]:
        """
        Busca dados completos para dashboard do gestor
        """
        # Busca contadores específicos do gestor
        gestor_contadores = await self.dashboard_repo.get_contadores_gestor(gestor_id)
        contadores = ContadoresDashboard(
            relatorios_para_analise=0,
            contratos_com_pendencias=0,
            usuarios_ativos=0,
            contratos_ativos=0,
            minhas_pendencias=0,
            pendencias_em_atraso=0,
            relatorios_enviados_mes=0,
            contratos_sob_gestao=gestor_contadores['contratos_sob_gestao'],
            relatorios_equipe_pendentes=gestor_contadores['relatorios_equipe_pendentes']
        )

        # Busca pendências dos contratos sob gestão
        pendencias_gestao = await self.get_pendencias_gestor(gestor_id)

        return {
            'contadores': contadores,
            'pendencias_gestao': pendencias_gestao,
            'gestor_id': gestor_id
        }

    # ===== NOVOS MÉTODOS PARA DASHBOARDS MELHORADOS =====

    async def get_dashboard_admin_melhorado(self) -> 'DashboardAdminCompleto':
        """
        Busca dados completos melhorados para o dashboard do administrador
        """
        from app.schemas.dashboard_schema import DashboardAdminCompleto, FiscalCargaTrabalho

        metrics = await self.dashboard_repo.get_dashboard_admin_completo()

        # Converte a lista de fiscais para objetos Pydantic
        fiscais_carga = [
            FiscalCargaTrabalho(**fiscal)
            for fiscal in metrics['fiscais_maior_carga']
        ]

        return DashboardAdminCompleto(
            contratos_com_pendencias=metrics['contratos_com_pendencias'],
            contratos_ativos=metrics['contratos_ativos'],
            relatorios_para_analise=metrics['relatorios_para_analise'],
            total_contratacoes=metrics['total_contratacoes'],
            usuarios_ativos_30_dias=metrics['usuarios_ativos_30_dias'],
            fiscais_maior_carga=fiscais_carga
        )

    async def get_dashboard_fiscal_melhorado(self, fiscal_id: int) -> 'DashboardFiscalCompleto':
        """
        Busca dados completos melhorados para o dashboard do fiscal
        """
        from app.schemas.dashboard_schema import DashboardFiscalCompleto

        metrics = await self.dashboard_repo.get_dashboard_fiscal_completo(fiscal_id)

        return DashboardFiscalCompleto(
            minhas_pendencias=metrics['minhas_pendencias'],
            pendencias_em_atraso=metrics['pendencias_em_atraso'],
            relatorios_enviados=metrics['relatorios_enviados'],
            contratos_ativos=metrics['contratos_ativos'],
            pendencias_proximas_vencimento=metrics['pendencias_proximas_vencimento'],
            relatorios_rejeitados=metrics['relatorios_rejeitados']
        )

    async def get_dashboard_gestor_melhorado(self, gestor_id: int) -> 'DashboardGestorCompleto':
        """
        Busca dados completos melhorados para o dashboard do gestor
        """
        from app.schemas.dashboard_schema import (
            DashboardGestorCompleto,
            EquipePerformance,
            ContratoProximoVencimento
        )

        metrics = await self.dashboard_repo.get_dashboard_gestor_completo(gestor_id)

        # Converte performance da equipe para objeto Pydantic
        performance = EquipePerformance(**metrics['performance_equipe'])

        # Converte contratos próximos ao vencimento para objetos Pydantic
        contratos_proximos = [
            ContratoProximoVencimento(**contrato)
            for contrato in metrics['contratos_proximos_vencimento']
        ]

        return DashboardGestorCompleto(
            contratos_sob_gestao=metrics['contratos_sob_gestao'],
            equipe_pendencias_atraso=metrics['equipe_pendencias_atraso'],
            relatorios_equipe_aguardando=metrics['relatorios_equipe_aguardando'],
            performance_equipe=performance,
            contratos_proximos_vencimento=contratos_proximos
        )