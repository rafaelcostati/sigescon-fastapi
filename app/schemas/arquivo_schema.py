# app/schemas/arquivo_schema.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class Arquivo(BaseModel):
    id: int
    nome_arquivo: str
    tipo_arquivo: str | None
    tamanho_bytes: int | None
    contrato_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)