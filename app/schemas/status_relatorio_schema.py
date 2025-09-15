# app/schemas/status_relatorio_schema.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class StatusRelatorioBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=50)

class StatusRelatorioCreate(StatusRelatorioBase):
    pass

class StatusRelatorioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=50)

class StatusRelatorio(StatusRelatorioBase):
    id: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)