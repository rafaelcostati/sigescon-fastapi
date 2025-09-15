# app/services/perfil_service.py
from typing import List, Optional
from app.repositories.perfil_repo import PerfilRepository
from app.schemas.perfil_schema import Perfil, PerfilCreate

class PerfilService:
    def __init__(self, perfil_repo: PerfilRepository):
        self.perfil_repo = perfil_repo

    async def get_all(self) -> List[Perfil]:
        perfis_data = await self.perfil_repo.get_all_perfis()
        return [Perfil.model_validate(p) for p in perfis_data]

    async def create(self, perfil_create: PerfilCreate) -> Perfil:
        new_perfil_data = await self.perfil_repo.create_perfil(perfil_create.nome)
        return Perfil.model_validate(new_perfil_data)