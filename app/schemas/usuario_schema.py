# app/schemas/usuario_schema.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    cpf: str
    matricula: Optional[str] = None
    perfil_id: int

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    matricula: Optional[str] = None
    perfil_id: Optional[int] = None

class Usuario(UsuarioBase):
    id: int
    ativo: bool
    model_config = ConfigDict(from_attributes=True)