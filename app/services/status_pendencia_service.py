# app/services/status_pendencia_service.py
from typing import List, Optional
from app.repositories.status_pendencia_repo import StatusPendenciaRepository
from app.schemas.status_pendencia_schema import StatusPendencia

class StatusPendenciaService:
    def __init__(self, repo: StatusPendenciaRepository):
        self.repo = repo

    async def get_all(self) -> List[StatusPendencia]:
        records = await self.repo.get_all()
        return [StatusPendencia.model_validate(r) for r in records]

    async def get_by_id(self, status_id: int) -> Optional[StatusPendencia]:
        record = await self.repo.get_by_id(status_id)
        if record:
            return StatusPendencia.model_validate(record)
        return None