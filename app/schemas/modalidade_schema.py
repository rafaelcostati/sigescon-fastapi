# app/schemas/modalidade_schema.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class ModalidadeBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)

class ModalidadeCreate(ModalidadeBase):
    pass

class ModalidadeUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=100)

class Modalidade(ModalidadeBase):
    id: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)