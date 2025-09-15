# app/schemas/pendencia_schema.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime

class PendenciaBase(BaseModel):
    descricao: str
    data_prazo: date
    status_pendencia_id: int
    criado_por_usuario_id: int

class PendenciaCreate(PendenciaBase):
    pass

class Pendencia(PendenciaBase):
    id: int
    contrato_id: int
    created_at: datetime
    updated_at: datetime
    
    # Campos de JOINs para exibição
    status_nome: Optional[str] = None
    criado_por_nome: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)