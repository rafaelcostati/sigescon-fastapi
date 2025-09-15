# app/schemas/usuario_schema.py
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime
import re

class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=255, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="Email único do usuário")
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF sem formatação")
    matricula: Optional[str] = Field(None, max_length=20, description="Matrícula do usuário")
    perfil_id: int = Field(..., gt=0, description="ID do perfil do usuário")

    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """Remove formatação e valida o CPF"""
        # Remove caracteres não numéricos
        cpf = re.sub(r'\D', '', v)
        
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        
        # Validação básica - evita CPFs como 11111111111
        if len(set(cpf)) == 1:
            raise ValueError('CPF inválido')
            
        return cpf

class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, description="Senha do usuário")

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    matricula: Optional[str] = Field(None, max_length=20)
    perfil_id: Optional[int] = Field(None, gt=0)
    senha: Optional[str] = Field(None, min_length=6)

    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        """Valida CPF se fornecido"""
        if v is None:
            return v
            
        cpf = re.sub(r'\D', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        if len(set(cpf)) == 1:
            raise ValueError('CPF inválido')
        return cpf

class UsuarioChangePassword(BaseModel):
    senha_antiga: str = Field(..., description="Senha atual do usuário")
    nova_senha: str = Field(..., min_length=6, description="Nova senha")

class UsuarioResetPassword(BaseModel):
    nova_senha: str = Field(..., min_length=6, description="Nova senha para o usuário")

class Usuario(UsuarioBase):
    id: int
    ativo: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class UsuarioWithPerfil(Usuario):
    """Schema estendido com informações do perfil"""
    perfil_nome: Optional[str] = None
    
class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str