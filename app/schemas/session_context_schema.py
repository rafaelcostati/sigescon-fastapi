# app/schemas/session_context_schema.py
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime

class PerfilAtivo(BaseModel):
    """Representação de um perfil ativo do usuário"""
    id: int
    nome: str
    pode_ser_selecionado: bool = True
    descricao: Optional[str] = None

class ContextoSessao(BaseModel):
    """Contexto atual da sessão do usuário"""
    usuario_id: int
    perfil_ativo_id: int
    perfil_ativo_nome: str
    perfis_disponiveis: List[PerfilAtivo]
    pode_alternar: bool = True
    sessao_id: str
    data_ultima_alternancia: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class AlternarPerfilRequest(BaseModel):
    """Request para alternar perfil na sessão"""
    novo_perfil_id: int = Field(..., description="ID do perfil para alternar")
    justificativa: Optional[str] = Field(None, description="Motivo da alternância (opcional)")

class LoginComPerfilRequest(BaseModel):
    """Request de login especificando perfil inicial"""
    email: str
    senha: str
    perfil_inicial_id: Optional[int] = Field(None, description="Perfil para iniciar sessão")

class RefreshTokenRequest(BaseModel):
    """Requisição para renovar token de acesso"""
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    """Resposta da renovação de token"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

class LoginResponse(BaseModel):
    """Resposta do login com informações de contexto"""
    access_token: str
    token_type: str = "bearer"
    contexto_sessao: ContextoSessao
    requer_selecao_perfil: bool = False
    mensagem: Optional[str] = None
    refresh_token: Optional[str] = None

class PerfilSwitchHistoryItem(BaseModel):
    """Item do histórico de alternância de perfis"""
    id: int
    usuario_id: int
    perfil_anterior_nome: str
    perfil_novo_nome: str
    data_alternancia: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    justificativa: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class DashboardData(BaseModel):
    """Dados do dashboard baseados no perfil ativo"""
    perfil_ativo: str
    widgets_disponiveis: List[str]
    menus_disponiveis: List[dict]
    permissoes_ativas: List[str]
    estatisticas: dict
    notificacoes: List[dict] = Field(default_factory=list)

class PermissaoContextual(BaseModel):
    """Permissões baseadas no contexto atual"""
    perfil_ativo: str
    pode_criar_contrato: bool = False
    pode_editar_contrato: bool = False
    pode_criar_pendencia: bool = False
    pode_submeter_relatorio: bool = False
    pode_aprovar_relatorio: bool = False
    pode_gerenciar_usuarios: bool = False
    pode_ver_todos_contratos: bool = False
    contratos_visiveis: List[int] = Field(default_factory=list)
    acoes_disponiveis: List[str] = Field(default_factory=list)