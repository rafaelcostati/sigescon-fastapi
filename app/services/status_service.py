# app/services/status_service.py
from typing import List, Optional
from fastapi import HTTPException, status

from app.repositories.status_repo import StatusRepository
from app.schemas.status_schema import Status, StatusCreate, StatusUpdate

class StatusService:
    def __init__(self, status_repo: StatusRepository):
        self.status_repo = status_repo

    async def get_all(self) -> List[Status]:
        status_data = await self.status_repo.get_all_status()
        return [Status.model_validate(s) for s in status_data]

    async def create(self, status_create: StatusCreate) -> Status:
        new_status_data = await self.status_repo.create_status(status_create.nome)
        return Status.model_validate(new_status_data)

    async def update(self, status_id: int, status_update: StatusUpdate) -> Optional[Status]:
        if not await self.status_repo.get_status_by_id(status_id):
            return None
        
        updated_data = await self.status_repo.update_status(status_id, status_update)
        return Status.model_validate(updated_data)

    async def delete(self, status_id: int) -> bool:
        if await self.status_repo.is_status_in_use(status_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este status não pode ser excluído pois está associado a um ou mais contratos."
            )
        
        deleted = await self.status_repo.delete_status(status_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status não encontrado")
        return True