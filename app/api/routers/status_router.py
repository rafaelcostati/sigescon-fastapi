# app/api/routers/status_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List

from app.core.database import get_connection
from app.schemas.status_schema import Status, StatusCreate, StatusUpdate
from app.services.status_service import StatusService
from app.repositories.status_repo import StatusRepository
from app.api.dependencies import get_current_user, get_current_admin_user
from app.schemas.usuario_schema import Usuario
from app.api.permissions import admin_required

router = APIRouter(
    prefix="/status",
    tags=["Status de Contratos"]
)

def get_status_service(conn: asyncpg.Connection = Depends(get_connection)):
    repo = StatusRepository(conn)
    return StatusService(repo)

@router.post("/", response_model=Status, status_code=status.HTTP_201_CREATED)
async def create_status(
    status_data: StatusCreate,
    service: StatusService = Depends(get_status_service),
    admin_user: Usuario = Depends(admin_required)
):
    try:
        return await service.create(status_data)
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um status com este nome já existe"
        )

# Rota com barra final (original)
@router.get("/", response_model=List[Status])
async def get_all_status_with_slash(
    service: StatusService = Depends(get_status_service),
    current_user: Usuario = Depends(get_current_user)
):
    return await service.get_all()

# Rota sem barra final (para evitar redirects do frontend)
@router.get("", response_model=List[Status])
async def get_all_status_without_slash(
    service: StatusService = Depends(get_status_service),
    current_user: Usuario = Depends(get_current_user)
):
    return await service.get_all()

@router.patch("/{status_id}", response_model=Status)
async def update_status(
    status_id: int,
    status_data: StatusUpdate,
    service: StatusService = Depends(get_status_service),
    admin_user: Usuario = Depends(admin_required)
):
    updated = await service.update(status_id, status_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Status não encontrado"
        )
    return updated

@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_status(
    status_id: int,
    service: StatusService = Depends(get_status_service),
    admin_user: Usuario = Depends(admin_required)
):
    await service.delete(status_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)