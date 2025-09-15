# app/schemas/status_pendencia_schema.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class StatusPendenciaBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=50)

class StatusPendenciaCreate(StatusPendenciaBase):
    pass

class StatusPendencia(StatusPendenciaBase):
    id: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)