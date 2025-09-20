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