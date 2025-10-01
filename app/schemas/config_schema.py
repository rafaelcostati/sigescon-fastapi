# app/schemas/config_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List
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

class AlertasVencimentoConfig(BaseModel):
    """Configurações de alertas de vencimento de contratos"""
    ativo: bool = Field(..., description="Se os alertas estão ativos")
    dias_antes: int = Field(..., ge=1, le=365, description="Quantos dias antes do vencimento começar os alertas (1-365)")
    periodicidade_dias: int = Field(..., ge=1, le=90, description="A cada quantos dias reenviar o alerta (1-90)")
    perfis_destino: List[str] = Field(..., description="Perfis que receberão os alertas: Administrador, Gestor, Fiscal")
    hora_envio: str = Field(..., description="Hora do dia para enviar (formato HH:MM)")

    class Config:
        json_schema_extra = {
            "example": {
                "ativo": True,
                "dias_antes": 90,
                "periodicidade_dias": 30,
                "perfis_destino": ["Administrador", "Gestor"],
                "hora_envio": "10:00"
            }
        }

class AlertasVencimentoConfigUpdate(BaseModel):
    """Schema para atualizar configurações de alertas de vencimento"""
    ativo: bool = Field(..., description="Se os alertas estão ativos")
    dias_antes: int = Field(..., ge=1, le=365, description="Quantos dias antes do vencimento começar os alertas (1-365)")
    periodicidade_dias: int = Field(..., ge=1, le=90, description="A cada quantos dias reenviar o alerta (1-90)")
    perfis_destino: List[str] = Field(..., description="Perfis que receberão os alertas")
    hora_envio: str = Field(..., pattern=r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', description="Hora do dia para enviar (formato HH:MM)")

    class Config:
        json_schema_extra = {
            "example": {
                "ativo": True,
                "dias_antes": 90,
                "periodicidade_dias": 30,
                "perfis_destino": ["Gestor", "Fiscal"],
                "hora_envio": "10:00"
            }
        }
