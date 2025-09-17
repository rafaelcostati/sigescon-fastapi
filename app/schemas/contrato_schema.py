# app/schemas/contrato_schema.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date

# Schema base com os campos comuns
class ContratoBase(BaseModel):
    nr_contrato: str = Field(..., max_length=50)
    objeto: str
    data_inicio: date
    data_fim: date
    contratado_id: int
    modalidade_id: int
    status_id: int
    gestor_id: int
    fiscal_id: int
    valor_anual: Optional[float] = None
    valor_global: Optional[float] = None
    base_legal: Optional[str] = Field(None, max_length=255)
    termos_contratuais: Optional[str] = None
    fiscal_substituto_id: Optional[int] = None
    pae: Optional[str] = Field(None, max_length=50)
    doe: Optional[str] = Field(None, max_length=50)
    data_doe: Optional[date] = None

# Schema para a resposta da API (leitura de um contrato)
# Inclui campos de tabelas relacionadas (JOINs)
class Contrato(ContratoBase):
    id: int
    ativo: bool
    contratado_nome: Optional[str] = None
    modalidade_nome: Optional[str] = None
    status_nome: Optional[str] = None
    gestor_nome: Optional[str] = None
    fiscal_nome: Optional[str] = None
    fiscal_substituto_nome: Optional[str] = None
    documento_nome_arquivo: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Schema para a criação de um novo contrato 
class ContratoCreate(ContratoBase):
    pass

# Schema para atualização 
class ContratoUpdate(BaseModel):
    nr_contrato: Optional[str] = Field(None, max_length=50)
    objeto: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    contratado_id: Optional[int] = None
    modalidade_id: Optional[int] = None
    status_id: Optional[int] = None
    gestor_id: Optional[int] = None
    fiscal_id: Optional[int] = None
    valor_anual: Optional[float] = None
    valor_global: Optional[float] = None
    base_legal: Optional[str] = Field(None, max_length=255)
    termos_contratuais: Optional[str] = None
    fiscal_substituto_id: Optional[int] = None
    pae: Optional[str] = Field(None, max_length=50)
    doe: Optional[str] = Field(None, max_length=50)
    data_doe: Optional[date] = None

# Schema para a resposta da listagem 
class ContratoList(BaseModel):
    id: int
    nr_contrato: str
    objeto: str
    data_fim: date
    contratado_nome: Optional[str] = None
    status_nome: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Schema para a resposta paginada da API
class ContratoPaginated(BaseModel):
    data: List[ContratoList]
    total_items: int
    total_pages: int
    current_page: int
    per_page: int