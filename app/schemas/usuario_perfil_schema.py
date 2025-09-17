# app/schemas/usuario_perfil_schema.py
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime

class UsuarioPerfilBase(BaseModel):
    usuario_id: int = Field(..., description="ID do usuário")
    perfil_id: int = Field(..., description="ID do perfil")

class UsuarioPerfilCreate(UsuarioPerfilBase):
    observacoes: Optional[str] = Field(None, description="Justificativa para concessão do perfil")

class UsuarioPerfilGrantRequest(BaseModel):
    perfil_ids: List[int] = Field(..., description="Lista de IDs dos perfis a conceder")
    observacoes: Optional[str] = Field(None, description="Justificativa para concessão dos perfis")

class UsuarioPerfilRevokeRequest(BaseModel):
    perfil_ids: List[int] = Field(..., description="Lista de IDs dos perfis a revogar")

class UsuarioPerfil(UsuarioPerfilBase):
    id: int
    ativo: bool = True  # Campo com valor padrão
    perfil_nome: str
    data_concessao: datetime
    observacoes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class UsuarioComPerfis(BaseModel):
    """Schema para usuário com todos os seus perfis"""
    id: int
    nome: str
    email: str
    matricula: Optional[str] = None
    ativo: bool
    perfis: List[str] = Field(default_factory=list, description="Lista de nomes dos perfis")
    perfil_ids: List[int] = Field(default_factory=list, description="Lista de IDs dos perfis")
    perfis_texto: str = Field(default="", description="Perfis concatenados em texto")
    
    model_config = ConfigDict(from_attributes=True)

class PerfilWithUsers(BaseModel):
    """Schema para perfil com lista de usuários que o possuem"""
    id: int
    nome: str
    ativo: bool
    usuarios: List[dict] = Field(default_factory=list, description="Usuários com este perfil")
    total_usuarios: int = Field(default=0, description="Total de usuários com este perfil")
    
    model_config = ConfigDict(from_attributes=True)

class HistoricoPerfilConcessao(BaseModel):
    """Schema para histórico de concessão/remoção de perfis"""
    id: int
    usuario_id: int
    perfil_id: int
    perfil_nome: str
    ativo: bool
    data_concessao: datetime
    concedido_por_usuario_id: Optional[int] = None
    concedido_por_nome: Optional[str] = None
    observacoes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ValidacaoPerfil(BaseModel):
    """Schema para resposta de validação de perfis"""
    usuario_id: int
    pode_ser_fiscal: bool
    pode_ser_gestor: bool
    pode_ser_admin: bool
    perfis_ativos: List[str]
    observacoes: Optional[str] = None