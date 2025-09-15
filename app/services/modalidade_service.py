# app/services/modalidade_service.py
from typing import List, Optional
from fastapi import HTTPException, status

from app.repositories.modalidade_repo import ModalidadeRepository
from app.schemas.modalidade_schema import Modalidade, ModalidadeCreate, ModalidadeUpdate

class ModalidadeService:
    def __init__(self, modalidade_repo: ModalidadeRepository):
        self.modalidade_repo = modalidade_repo

    async def get_all(self) -> List[Modalidade]:
        modalidades_data = await self.modalidade_repo.get_all_modalidades()
        return [Modalidade.model_validate(m) for m in modalidades_data]
    
    async def get_by_id(self, modalidade_id: int) -> Optional[Modalidade]:
        modalidade_data = await self.modalidade_repo.get_modalidade_by_id(modalidade_id)
        if modalidade_data:
            return Modalidade.model_validate(modalidade_data)
        return None

    async def create(self, modalidade_create: ModalidadeCreate) -> Modalidade:
        new_modalidade_data = await self.modalidade_repo.create_modalidade(modalidade_create.nome)
        return Modalidade.model_validate(new_modalidade_data)

    async def update(self, modalidade_id: int, modalidade_update: ModalidadeUpdate) -> Optional[Modalidade]:
        if not await self.modalidade_repo.get_modalidade_by_id(modalidade_id):
            return None
        
        updated_data = await self.modalidade_repo.update_modalidade(modalidade_id, modalidade_update)
        return Modalidade.model_validate(updated_data)

    async def delete(self, modalidade_id: int) -> bool:
        # Lógica de Negócio: não permitir exclusão se a modalidade estiver em uso.
        if await self.modalidade_repo.is_modalidade_in_use(modalidade_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta modalidade não pode ser excluída pois está associada a um ou mais contratos."
            )
        
        deleted = await self.modalidade_repo.delete_modalidade(modalidade_id)
        if not deleted:
            # Lança exceção se não encontrou para deletar, o que significa que o ID não existe
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modalidade não encontrada")
        return True