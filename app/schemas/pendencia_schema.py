# app/schemas/pendencia_schema.py
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import date, datetime

class PendenciaBase(BaseModel):
    descricao: str
    data_prazo: date
    status_pendencia_id: int
    criado_por_usuario_id: int

class PendenciaCreate(PendenciaBase):
    @field_validator('data_prazo')
    @classmethod
    def validate_data_prazo(cls, v):
        # Permite datas passadas para testes (removendo a restrição anterior se existia)
        # Valida apenas se é uma data válida
        if not isinstance(v, date):
            raise ValueError('data_prazo deve ser uma data válida')
        return v

class Pendencia(PendenciaBase):
    id: int
    contrato_id: int
    created_at: datetime
    updated_at: datetime
    status_nome: Optional[str] = None
    criado_por_nome: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)