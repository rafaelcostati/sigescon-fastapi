# app/services/contratado_service.py
from typing import List, Optional
from app.repositories.contratado_repo import ContratadoRepository
from app.schemas.contratado_schema import Contratado, ContratadoCreate, ContratadoUpdate

class ContratadoService:
    def __init__(self, contratado_repo: ContratadoRepository):
        self.contratado_repo = contratado_repo

    async def get_all(self) -> List[Contratado]:
        contratados_data = await self.contratado_repo.get_all_contratados()
        return [Contratado.model_validate(c) for c in contratados_data]

    async def get_by_id(self, contratado_id: int) -> Optional[Contratado]:
        contratado_data = await self.contratado_repo.get_contratado_by_id(contratado_id)
        if contratado_data:
            return Contratado.model_validate(contratado_data)
        return None

    async def create(self, contratado_create: ContratadoCreate) -> Contratado:
        new_contratado_data = await self.contratado_repo.create_contratado(contratado_create)
        return Contratado.model_validate(new_contratado_data)

    # --- NOVO MÉTODO DE ATUALIZAÇÃO ---
    async def update(self, contratado_id: int, contratado_update: ContratadoUpdate) -> Optional[Contratado]:
        # Lógica de negócio: Primeiro, verifica se o contratado existe
        contratado_existente = await self.contratado_repo.get_contratado_by_id(contratado_id)
        if not contratado_existente:
            return None
        
        updated_data = await self.contratado_repo.update_contratado(contratado_id, contratado_update)
        return Contratado.model_validate(updated_data)

    # --- NOVO MÉTODO DE EXCLUSÃO ---
    async def delete(self, contratado_id: int) -> bool:
        # Lógica de negócio: Verifica se o contratado existe antes de tentar deletar
        contratado_existente = await self.contratado_repo.get_contratado_by_id(contratado_id)
        if not contratado_existente:
            return False # Retorna False se não encontrou para deletar
            
        return await self.contratado_repo.delete_contratado(contratado_id)