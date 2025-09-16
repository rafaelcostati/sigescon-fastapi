# app/api/routers/modalidade_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List

from app.core.database import get_connection
from app.schemas.modalidade_schema import Modalidade, ModalidadeCreate, ModalidadeUpdate
from app.services.modalidade_service import ModalidadeService
from app.repositories.modalidade_repo import ModalidadeRepository
from app.api.dependencies import get_current_user, get_current_admin_user
from app.schemas.usuario_schema import Usuario
from app.api.permissions import admin_required

router = APIRouter(
    prefix="/modalidades",
    tags=["Modalidades"]
)

def get_modalidade_service(conn: asyncpg.Connection = Depends(get_connection)):
    repo = ModalidadeRepository(conn)
    return ModalidadeService(repo)

@router.post("/", response_model=Modalidade, status_code=status.HTTP_201_CREATED)
async def create_modalidade(
    modalidade: ModalidadeCreate,
    service: ModalidadeService = Depends(get_modalidade_service),
    admin_user: Usuario = Depends(admin_required)
):
    try:
        return await service.create(modalidade)
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uma modalidade com este nome já existe"
        )

@router.get("/", response_model=List[Modalidade])
async def get_all_modalidades(
    service: ModalidadeService = Depends(get_modalidade_service),
    current_user: Usuario = Depends(get_current_user)
):
    return await service.get_all()

@router.patch("/{modalidade_id}", response_model=Modalidade)
async def update_modalidade(
    modalidade_id: int,
    modalidade: ModalidadeUpdate,
    service: ModalidadeService = Depends(get_modalidade_service),
    admin_user: Usuario = Depends(admin_required)
):
    updated = await service.update(modalidade_id, modalidade)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modalidade não encontrada"
        )
    return updated

@router.delete("/{modalidade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modalidade(
    modalidade_id: int,
    service: ModalidadeService = Depends(get_modalidade_service),
    admin_user: Usuario = Depends(admin_required)
):
    await service.delete(modalidade_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)