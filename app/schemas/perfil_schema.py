# app/schemas/perfil_schema.py
from pydantic import BaseModel, ConfigDict

class PerfilBase(BaseModel):
    nome: str

class PerfilCreate(PerfilBase):
    pass

class Perfil(PerfilBase):
    id: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)