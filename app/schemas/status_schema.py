# app/schemas/status_schema.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class StatusBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=50)

class StatusCreate(StatusBase):
    pass

class StatusUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=50)

class Status(StatusBase):
    id: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)