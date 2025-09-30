# app/schemas/config_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ConfigBase(BaseModel):
    chave: str = Field(..., description="Chave única da configuração")
    valor: str = Field(..., description="Valor da configuração")
    descricao: Optional[str] = Field(None, description="Descrição da configuração")
    tipo: str = Field(default='string', description="Tipo de dado: string, integer, boolean, json")

class ConfigCreate(ConfigBase):
    pass

class ConfigUpdate(BaseModel):
    valor: str = Field(..., description="Novo valor da configuração")

class Config(ConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PendenciasIntervaloDiasUpdate(BaseModel):
    intervalo_dias: int = Field(..., ge=1, le=365, description="Intervalo em dias entre pendências automáticas (1-365)")
