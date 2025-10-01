"""
Schemas para logs de auditoria
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AcaoAuditoria(str, Enum):
    """Tipos de ações auditadas"""
    # CRUD
    CRIAR = "CRIAR"
    ATUALIZAR = "ATUALIZAR"
    DELETAR = "DELETAR"
    ATIVAR = "ATIVAR"
    DESATIVAR = "DESATIVAR"

    # Workflow
    APROVAR = "APROVAR"
    REJEITAR = "REJEITAR"
    ENVIAR = "ENVIAR"
    CONCLUIR = "CONCLUIR"
    CANCELAR = "CANCELAR"

    # Autenticação
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ALTERNAR_PERFIL = "ALTERNAR_PERFIL"

    # Arquivos
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"
    REMOVER_ARQUIVO = "REMOVER_ARQUIVO"

    # Especiais
    CRIAR_PENDENCIAS_AUTOMATICAS = "CRIAR_PENDENCIAS_AUTOMATICAS"
    ATUALIZAR_CONFIG = "ATUALIZAR_CONFIG"


class EntidadeAuditoria(str, Enum):
    """Tipos de entidades auditadas"""
    CONTRATO = "CONTRATO"
    PENDENCIA = "PENDENCIA"
    RELATORIO = "RELATORIO"
    USUARIO = "USUARIO"
    PERFIL = "PERFIL"
    CONFIG = "CONFIG"
    ARQUIVO = "ARQUIVO"
    CONTRATADO = "CONTRATADO"
    SESSION = "SESSION"


# ==================== Request Schemas ====================

class AuditLogCreate(BaseModel):
    """Schema para criar um log de auditoria"""
    usuario_id: int = Field(..., description="ID do usuário que realizou a ação")
    usuario_nome: str = Field(..., description="Nome do usuário")
    perfil_usado: Optional[str] = Field(None, description="Perfil ativo no momento")

    acao: AcaoAuditoria = Field(..., description="Tipo de ação")
    entidade: EntidadeAuditoria = Field(..., description="Tipo de entidade")
    entidade_id: Optional[int] = Field(None, description="ID da entidade afetada")

    descricao: str = Field(..., description="Descrição legível da ação")
    dados_anteriores: Optional[Dict[str, Any]] = Field(None, description="Estado anterior")
    dados_novos: Optional[Dict[str, Any]] = Field(None, description="Estado novo")

    ip_address: Optional[str] = Field(None, max_length=45, description="IP do cliente")
    user_agent: Optional[str] = Field(None, description="User agent do navegador")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# ==================== Response Schemas ====================

class AuditLog(BaseModel):
    """Schema de resposta de log de auditoria"""
    id: int
    usuario_id: int
    usuario_nome: str
    perfil_usado: Optional[str] = None

    acao: str
    entidade: str
    entidade_id: Optional[int] = None

    descricao: str
    dados_anteriores: Optional[Dict[str, Any]] = None
    dados_novos: Optional[Dict[str, Any]] = None

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogList(BaseModel):
    """Schema de resposta de lista de logs"""
    logs: List[AuditLog]
    total: int
    pagina: int
    tamanho_pagina: int
    total_paginas: int

    model_config = ConfigDict(from_attributes=True)


# ==================== Filter Schemas ====================

class AuditLogFilter(BaseModel):
    """Filtros para consulta de logs de auditoria"""
    usuario_id: Optional[int] = Field(None, description="Filtrar por usuário")
    perfil: Optional[str] = Field(None, description="Filtrar por perfil")
    acao: Optional[AcaoAuditoria] = Field(None, description="Filtrar por ação")
    entidade: Optional[EntidadeAuditoria] = Field(None, description="Filtrar por entidade")
    entidade_id: Optional[int] = Field(None, description="Filtrar por ID da entidade")

    data_inicio: Optional[datetime] = Field(None, description="Data inicial (YYYY-MM-DD)")
    data_fim: Optional[datetime] = Field(None, description="Data final (YYYY-MM-DD)")

    busca: Optional[str] = Field(None, description="Busca na descrição")

    # Paginação
    pagina: int = Field(1, ge=1, description="Número da página")
    tamanho_pagina: int = Field(50, ge=1, le=100, description="Tamanho da página")

    # Ordenação
    ordenar_por: str = Field("data_hora", description="Campo para ordenar")
    ordem: str = Field("DESC", description="ASC ou DESC")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# ==================== Statistics Schemas ====================

class AuditStatistics(BaseModel):
    """Estatísticas de auditoria"""
    total_logs: int
    logs_por_acao: Dict[str, int]
    logs_por_entidade: Dict[str, int]
    logs_por_usuario: List[Dict[str, Any]]  # Top 10 usuários mais ativos
    logs_ultimas_24h: int
    logs_ultima_semana: int

    model_config = ConfigDict(from_attributes=True)
