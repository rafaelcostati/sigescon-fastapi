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

class LembretesConfigUpdate(BaseModel):
    dias_antes_vencimento_inicio: int = Field(..., ge=1, le=90, description="Quantos dias antes do vencimento começar a enviar lembretes (1-90)")
    intervalo_dias_lembrete: int = Field(..., ge=1, le=30, description="A cada quantos dias enviar lembretes (1-30)")

class ModeloRelatorioInfo(BaseModel):
    """Informações sobre o modelo de relatório ativo"""
    arquivo_id: int = Field(..., description="ID do arquivo modelo no sistema")
    nome_original: str = Field(..., description="Nome original do arquivo")
    ativo: bool = Field(True, description="Indica se o modelo está ativo")

class ModeloRelatorioResponse(BaseModel):
    """Resposta após operações com modelo de relatório"""
    success: bool = Field(..., description="Indica se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem descritiva da operação")
    modelo: Optional[ModeloRelatorioInfo] = Field(None, description="Informações do modelo (quando aplicável)")
