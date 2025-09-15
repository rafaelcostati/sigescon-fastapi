# app/services/status_relatorio_service.py
from typing import List, Optional
from app.repositories.status_relatorio_repo import StatusRelatorioRepository
from app.schemas.status_relatorio_schema import StatusRelatorio

class StatusRelatorioService:
    def __init__(self, repo: StatusRelatorioRepository):
        self.repo = repo

    async def get_all(self) -> List[StatusRelatorio]:
        records = await self.repo.get_all()
        return [StatusRelatorio.model_validate(r) for r in records]

    async def get_by_id(self, status_id: int) -> Optional[StatusRelatorio]:
        record = await self.repo.get_by_id(status_id)
        if record:
            return StatusRelatorio.model_validate(record)
        return None