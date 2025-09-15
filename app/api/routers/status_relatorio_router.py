# app/api/routers/status_relatorio_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.database import get_connection
from app.schemas.status_relatorio_schema import StatusRelatorio
from app.services.status_relatorio_service import StatusRelatorioService
from app.repositories.status_relatorio_repo import StatusRelatorioRepository
from app.api.dependencies import get_current_user
from app.schemas.usuario_schema import Usuario

router = APIRouter(
    prefix="/statusrelatorio",
    tags=["Status de Relatórios"]
)

def get_service(conn: asyncpg.Connection = Depends(get_connection)):
    repo = StatusRelatorioRepository(conn)
    return StatusRelatorioService(repo)

@router.get("/", response_model=List[StatusRelatorio])
async def get_all_status_relatorio(
    service: StatusRelatorioService = Depends(get_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos os status de relatório disponíveis no sistema."""
    return await service.get_all()

@router.get("/{status_id}", response_model=StatusRelatorio)
async def get_status_relatorio_by_id(
    status_id: int,
    service: StatusRelatorioService = Depends(get_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Busca um status de relatório específico pelo ID."""
    status = await service.get_by_id(status_id)
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Status de relatório não encontrado"
        )
    return status