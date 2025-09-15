# app/api/routers/contratado_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List

from app.core.database import get_connection
from app.schemas.contratado_schema import Contratado, ContratadoCreate, ContratadoUpdate
from app.services.contratado_service import ContratadoService
from app.repositories.contratado_repo import ContratadoRepository

router = APIRouter(
    prefix="/contratados",
    tags=["Contratados"]
)

# Função de dependência para obter o serviço de contratado
def get_contratado_service(conn: asyncpg.Connection = Depends(get_connection)):
    repo = ContratadoRepository(conn)
    return ContratadoService(repo)

@router.post("/", response_model=Contratado, status_code=status.HTTP_201_CREATED)
async def create_contratado(
    contratado: ContratadoCreate,
    service: ContratadoService = Depends(get_contratado_service)
):
    return await service.create(contratado)

@router.get("/", response_model=List[Contratado])
async def get_all_contratados(
    service: ContratadoService = Depends(get_contratado_service)
):
    return await service.get_all()

@router.get("/{contratado_id}", response_model=Contratado)
async def get_contratado_by_id(
    contratado_id: int,
    service: ContratadoService = Depends(get_contratado_service)
):
    contratado = await service.get_by_id(contratado_id)
    if not contratado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratado não encontrado"
        )
    return contratado

# --- NOVO ENDPOINT DE ATUALIZAÇÃO ---
@router.patch("/{contratado_id}", response_model=Contratado)
async def update_contratado(
    contratado_id: int,
    contratado: ContratadoUpdate,
    service: ContratadoService = Depends(get_contratado_service)
):
    updated_contratado = await service.update(contratado_id, contratado)
    if not updated_contratado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratado não encontrado para atualização"
        )
    return updated_contratado

# --- NOVO ENDPOINT DE EXCLUSÃO ---
@router.delete("/{contratado_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contratado(
    contratado_id: int,
    service: ContratadoService = Depends(get_contratado_service)
):
    deleted = await service.delete(contratado_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratado não encontrado para exclusão"
        )
    # Retorna uma resposta vazia com status 204, como é a boa prática para DELETE
    return Response(status_code=status.HTTP_204_NO_CONTENT)