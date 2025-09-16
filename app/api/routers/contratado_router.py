# app/api/routers/contratado_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from typing import List, Optional

from app.core.database import get_connection
from app.schemas.contratado_schema import Contratado, ContratadoCreate, ContratadoUpdate, ContratadoPaginated
from app.services.contratado_service import ContratadoService
from app.repositories.contratado_repo import ContratadoRepository
from app.api.dependencies import get_current_user, get_current_admin_user
from app.schemas.usuario_schema import Usuario
from app.api.permissions import admin_required

router = APIRouter(
    prefix="/contratados",
    tags=["Contratados"]
)

def get_contratado_service(conn: asyncpg.Connection = Depends(get_connection)):
    repo = ContratadoRepository(conn)
    return ContratadoService(repo)

@router.post("/", response_model=Contratado, status_code=status.HTTP_201_CREATED)
async def create_contratado(
    contratado: ContratadoCreate,
    service: ContratadoService = Depends(get_contratado_service),
    admin_user: Usuario = Depends(admin_required)
):
    return await service.create(contratado)

@router.get("/", response_model=ContratadoPaginated)
async def get_all_contratados(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(10, ge=1, le=100, description="Itens por página"),
    nome: Optional[str] = Query(None, description="Filtrar por nome"),
    cnpj: Optional[str] = Query(None, description="Filtrar por CNPJ"),
    cpf: Optional[str] = Query(None, description="Filtrar por CPF"),
    service: ContratadoService = Depends(get_contratado_service),
    current_user: Usuario = Depends(get_current_user)
):
    filters = {
        'nome': nome,
        'cnpj': cnpj,
        'cpf': cpf
    }
    active_filters = {k: v for k, v in filters.items() if v is not None}
    
    return await service.get_all_paginated(
        page=page, 
        per_page=per_page, 
        filters=active_filters
    )

@router.get("/{contratado_id}", response_model=Contratado)
async def get_contratado_by_id(
    contratado_id: int,
    service: ContratadoService = Depends(get_contratado_service),
    current_user: Usuario = Depends(get_current_user)
):
    contratado = await service.get_by_id(contratado_id)
    if not contratado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratado não encontrado"
        )
    return contratado

@router.patch("/{contratado_id}", response_model=Contratado)
async def update_contratado(
    contratado_id: int,
    contratado: ContratadoUpdate,
    service: ContratadoService = Depends(get_contratado_service),
    admin_user: Usuario = Depends(admin_required)
):
    updated_contratado = await service.update(contratado_id, contratado)
    if not updated_contratado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratado não encontrado para atualização"
        )
    return updated_contratado

@router.delete("/{contratado_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contratado(
    contratado_id: int,
    service: ContratadoService = Depends(get_contratado_service),
    admin_user: Usuario = Depends(admin_required)
):
    deleted = await service.delete(contratado_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratado não encontrado para exclusão"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)