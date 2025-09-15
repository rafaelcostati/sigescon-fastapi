# app/api/routers/status_pendencia_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.database import get_connection
from app.schemas.status_pendencia_schema import StatusPendencia
from app.services.status_pendencia_service import StatusPendenciaService
from app.repositories.status_pendencia_repo import StatusPendenciaRepository
from app.api.dependencies import get_current_user
from app.schemas.usuario_schema import Usuario

router = APIRouter(
    prefix="/statuspendencia",
    tags=["Status de Pendências"]
)

def get_service(conn: asyncpg.Connection = Depends(get_connection)):
    repo = StatusPendenciaRepository(conn)
    return StatusPendenciaService(repo)

@router.get("/", response_model=List[StatusPendencia])
async def get_all_status_pendencia(
    service: StatusPendenciaService = Depends(get_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos os status de pendência disponíveis no sistema."""
    return await service.get_all()

@router.get("/{status_id}", response_model=StatusPendencia)
async def get_status_pendencia_by_id(
    status_id: int,
    service: StatusPendenciaService = Depends(get_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Busca um status de pendência específico pelo ID."""
    status = await service.get_by_id(status_id)
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Status de pendência não encontrado"
        )
    return status