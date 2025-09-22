# app/schemas/dashboard_schema.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime


class ContratoResumo(BaseModel):
    """Schema resumido de contrato para listagens de dashboard"""
    id: int
    nr_contrato: str
    objeto: str
    data_inicio: date
    data_fim: date
    contratado_nome: str
    gestor_nome: str
    fiscal_nome: str
    status_nome: str


class ContratoPendenciaResumo(ContratoResumo):
    """Contrato com informações de pendências"""
    pendencias_count: int
    pendencias_em_atraso: int
    ultima_pendencia_data: Optional[datetime]


class ContratoRelatorioResumo(ContratoResumo):
    """Contrato com informações de relatórios pendentes de análise"""
    relatorios_pendentes_count: int
    ultimo_relatorio_data: Optional[datetime]
    ultimo_relatorio_fiscal: Optional[str]


class ContratosComPendencias(BaseModel):
    """Response para lista de contratos com pendências"""
    contratos: List[ContratoPendenciaResumo]
    total_contratos: int
    total_pendencias: int


class ContratosComRelatoriosPendentes(BaseModel):
    """Response para lista de contratos com relatórios pendentes"""
    contratos: List[ContratoRelatorioResumo]
    total_contratos: int
    total_relatorios_pendentes: int


class MinhasPendencias(BaseModel):
    """Pendências do fiscal logado"""
    contrato_id: int
    contrato_numero: str
    contrato_objeto: str
    pendencia_id: int
    pendencia_titulo: str
    pendencia_descricao: str
    data_criacao: datetime
    prazo_entrega: Optional[date]
    dias_restantes: Optional[int]
    em_atraso: bool


class MinhasPendenciasResponse(BaseModel):
    """Response para pendências do fiscal"""
    pendencias: List[MinhasPendencias]
    total_pendencias: int
    pendencias_em_atraso: int
    pendencias_proximas_vencimento: int  # próximas 7 dias


class ContadoresDashboard(BaseModel):
    """Contadores gerais para dashboard por perfil"""
    # Para Administrador
    relatorios_para_analise: int
    contratos_com_pendencias: int
    usuarios_ativos: int
    contratos_ativos: int
    total_contratacoes: int
    contratados_com_pendencias_vencidas: int

    # Para Fiscal
    minhas_pendencias: int
    pendencias_em_atraso: int
    relatorios_enviados_mes: int

    # Para Gestor
    contratos_sob_gestao: int
    relatorios_equipe_pendentes: int


class DashboardAdminResponse(BaseModel):
    """Response completa para dashboard do administrador"""
    contadores: ContadoresDashboard
    contratos_com_relatorios_pendentes: List[ContratoRelatorioResumo]
    contratos_com_pendencias: List[ContratoPendenciaResumo]


class DashboardFiscalResponse(BaseModel):
    """Response completa para dashboard do fiscal"""
    contadores: ContadoresDashboard
    minhas_pendencias: List[MinhasPendencias]


class PendenciaVencidaAdmin(BaseModel):
    """Pendência vencida com informações completas para administrador"""
    pendencia_id: int
    titulo: str
    descricao: str
    data_criacao: datetime
    prazo_entrega: date
    dias_em_atraso: int

    # Informações do contrato
    contrato_id: int
    contrato_numero: str
    contrato_objeto: str

    # Responsáveis
    fiscal_nome: str
    gestor_nome: str

    # Classificação de urgência
    urgencia: str  # "CRÍTICA", "ALTA", "MÉDIA"


class PendenciasVencidasAdminResponse(BaseModel):
    """Response para pendências vencidas do administrador"""
    pendencias_vencidas: List[PendenciaVencidaAdmin]
    total_pendencias_vencidas: int
    contratos_afetados: int
    pendencias_criticas: int  # > 30 dias
    pendencias_altas: int     # 15-30 dias
    pendencias_medias: int    # 1-14 dias


# ===== NOVOS SCHEMAS PARA DASHBOARDS MELHORADOS =====

class FiscalCargaTrabalho(BaseModel):
    """Fiscal com informações de carga de trabalho"""
    fiscal_id: int
    fiscal_nome: str
    fiscal_email: str
    total_pendencias: int
    pendencias_vencidas: int
    contratos_ativos: int


class DashboardAdminCompleto(BaseModel):
    """Dashboard completo do administrador com todas as métricas"""
    # Métricas básicas
    contratos_com_pendencias: int
    contratos_ativos: int
    relatorios_para_analise: int
    total_contratacoes: int

    # Métricas adicionais solicitadas
    usuarios_ativos_30_dias: int
    fiscais_maior_carga: List[FiscalCargaTrabalho]


class DashboardFiscalCompleto(BaseModel):
    """Dashboard completo do fiscal com todas as métricas"""
    # Métricas básicas
    minhas_pendencias: int
    pendencias_em_atraso: int
    relatorios_enviados: int
    contratos_ativos: int

    # Métricas adicionais solicitadas
    pendencias_proximas_vencimento: int  # próximos 7 dias
    relatorios_rejeitados: int  # precisam reenvio


class EquipePerformance(BaseModel):
    """Performance da equipe do gestor"""
    total_fiscais: int
    fiscais_com_atraso: int
    taxa_cumprimento_prazos: float  # porcentagem
    pendencias_vencidas_equipe: int


class ContratoProximoVencimento(BaseModel):
    """Contrato próximo ao vencimento"""
    contrato_id: int
    numero: str
    objeto: str
    data_fim: date
    dias_restantes: int
    fiscal_nome: str


class DashboardGestorCompleto(BaseModel):
    """Dashboard completo do gestor com todas as métricas"""
    # Métricas solicitadas
    contratos_sob_gestao: int
    equipe_pendencias_atraso: int
    relatorios_equipe_aguardando: int
    performance_equipe: EquipePerformance
    contratos_proximos_vencimento: List[ContratoProximoVencimento]


class DashboardFiscalMelhorado(BaseModel):
    """Dashboard melhorado para fiscais com métricas específicas"""
    minhas_pendencias: int
    pendencias_em_atraso: int
    relatorios_enviados: int
    contratos_ativos: int
    pendencias_proximas_vencimento: int
    relatorios_rejeitados: int