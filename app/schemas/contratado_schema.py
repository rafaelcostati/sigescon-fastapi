# app/schemas/contratado_schema.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional

# Campos compartilhados por outros schemas
class ContratadoBase(BaseModel):
    nome: str
    email: EmailStr
    cnpj: Optional[str] = None
    cpf: Optional[str] = None
    telefone: Optional[str] = None

# Schema para criação
class ContratadoCreate(ContratadoBase):
    pass

# ---SCHEMA ---

class ContratadoUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cnpj: Optional[str] = None  
    cpf: Optional[str] = None   
    telefone: Optional[str] = None

# Schema para resposta 
class Contratado(ContratadoBase):
    id: int
    ativo: bool
    
    # Habilita o modo "ORM" para que o Pydantic consiga ler
    # os dados vindos do banco (que não são um dict puro)
    model_config = ConfigDict(from_attributes=True)
    
class ContratadoPaginated(BaseModel):
    data: List[Contratado]
    total_items: int
    total_pages: int
    current_page: int
    per_page: int