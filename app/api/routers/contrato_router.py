# app/api/routers/contrato_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.dependencies import get_current_user, get_current_admin_user

# Repositórios necessários para o serviço
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.contratado_repo import ContratadoRepository as ContratadoRepo
from app.repositories.modalidade_repo import ModalidadeRepository
from app.repositories.status_repo import StatusRepository

# Service e Schemas de Contrato
from app.services.contrato_service import ContratoService
from app.schemas.contrato_schema import (
    Contrato, ContratoCreate, ContratoUpdate, ContratoPaginated
)

router = APIRouter(
    prefix="/contratos",
    tags=["Contratos"]
)

# --- Injeção de Dependências ---
# Função complexa para injetar o ContratoService com todos os seus repositórios
def get_contrato_service(conn: asyncpg.Connection = Depends(get_connection)) -> ContratoService:
    contrato_repo = ContratoRepository(conn)
    usuario_repo = UsuarioRepository(conn)
    contratado_repo = ContratadoRepo(conn)
    modalidade_repo = ModalidadeRepository(conn)
    status_repo = StatusRepository(conn)
    return ContratoService(
        contrato_repo=contrato_repo,
        usuario_repo=usuario_repo,
        contratado_repo=contratado_repo,
        modalidade_repo=modalidade_repo,
        status_repo=status_repo
    )

# --- Endpoints ---

@router.post("/", response_model=Contrato, status_code=status.HTTP_201_CREATED)
async def create_contrato(
    contrato: ContratoCreate,
    service: ContratoService = Depends(get_contrato_service),
    admin_user: Usuario = Depends(get_current_admin_user)
):
    """Cria um novo contrato. Requer permissão de administrador."""
    # A lógica de upload de arquivo será adicionada aqui em um passo futuro
    return await service.create_contrato(contrato)

@router.get("/", response_model=ContratoPaginated)
async def list_contratos(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(10, ge=1, le=100, description="Itens por página"),
    gestor_id: Optional[int] = Query(None),
    fiscal_id: Optional[int] = Query(None),
    objeto: Optional[str] = Query(None),
    nr_contrato: Optional[str] = Query(None),
    status_id: Optional[int] = Query(None),
    pae: Optional[str] = Query(None),
    ano: Optional[int] = Query(None),
    service: ContratoService = Depends(get_contrato_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos os contratos com filtros e paginação. 
    Aberto para qualquer usuário autenticado.
    """
    filters = {
        'gestor_id': gestor_id,
        'fiscal_id': fiscal_id,
        'objeto': objeto,
        'nr_contrato': nr_contrato,
        'status_id': status_id,
        'pae': pae,
        'ano': ano
    }
    # Remove filtros não preenchidos
    active_filters = {k: v for k, v in filters.items() if v is not None}
    
    return await service.get_all_contratos(page=page, per_page=per_page, filters=active_filters)

@router.get("/{contrato_id}", response_model=Contrato)
async def get_contrato_by_id(
    contrato_id: int,
    service: ContratoService = Depends(get_contrato_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Busca um contrato específico pelo seu ID."""
    contrato = await service.get_contrato_by_id(contrato_id)
    if not contrato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    return contrato

@router.patch("/{contrato_id}", response_model=Contrato)
async def update_contrato(
    contrato_id: int,
    contrato_update: ContratoUpdate,
    service: ContratoService = Depends(get_contrato_service),
    admin_user: Usuario = Depends(get_current_admin_user)
):
    """Atualiza um contrato existente. Requer permissão de administrador."""
    updated_contrato = await service.update_contrato(contrato_id, contrato_update)
    if not updated_contrato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado para atualização"
        )
    return updated_contrato

@router.delete("/{contrato_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contrato(
    contrato_id: int,
    service: ContratoService = Depends(get_contrato_service),
    admin_user: Usuario = Depends(get_current_admin_user)
):
    """Realiza o soft delete de um contrato. Requer permissão de administrador."""
    await service.delete_contrato(contrato_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)