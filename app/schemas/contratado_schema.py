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

# Schema para criação (o que a API recebe no POST)
class ContratadoCreate(ContratadoBase):
    pass

# ---SCHEMA ---
# Schema para atualização (o que a API recebe no PATCH)
class ContratadoUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cnpj: Optional[str] = None  
    cpf: Optional[str] = None   
    telefone: Optional[str] = None

# Schema para resposta (o que a API envia de volta)
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