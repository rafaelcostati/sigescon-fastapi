# app/api/routers/pendencia_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.dependencies import get_current_user, get_current_admin_user
from app.api.permissions import admin_required, PermissionChecker


# Repositórios e Serviços
from app.repositories.pendencia_repo import PendenciaRepository
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.status_pendencia_repo import StatusPendenciaRepository
from app.services.pendencia_service import PendenciaService
from app.schemas.pendencia_schema import Pendencia, PendenciaCreate

router = APIRouter(
    prefix="/contratos/{contrato_id}/pendencias",
    tags=["Pendências"]
)

# --- Injeção de Dependências ---
def get_pendencia_service(conn: asyncpg.Connection = Depends(get_connection)) -> PendenciaService:
    return PendenciaService(
        pendencia_repo=PendenciaRepository(conn),
        contrato_repo=ContratoRepository(conn),
        usuario_repo=UsuarioRepository(conn),
        status_pendencia_repo=StatusPendenciaRepository(conn)
    )

# --- Endpoints ---

@router.post("/", response_model=Pendencia, status_code=status.HTTP_201_CREATED)
async def create_pendencia(
    contrato_id: int,
    pendencia: PendenciaCreate,
    service: PendenciaService = Depends(get_pendencia_service),
    admin_user: Usuario = Depends(admin_required)
):
    """Cria uma nova pendência para um contrato. Requer permissão de administrador."""
    return await service.create_pendencia(contrato_id, pendencia)


@router.get("/", response_model=List[Pendencia])
async def list_pendencias(
    contrato_id: int,
    service: PendenciaService = Depends(get_pendencia_service),
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
):
    # Verificação manual de permissão
    checker = PermissionChecker(conn)
    if not await checker.can_access_contract(current_user, contrato_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar este contrato"
        )
    
    return await service.get_pendencias_by_contrato_id(contrato_id)

@router.patch("/{pendencia_id}/cancelar", response_model=Pendencia)
async def cancelar_pendencia(
    contrato_id: int,
    pendencia_id: int,
    service: PendenciaService = Depends(get_pendencia_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Cancela uma pendência específica. Requer permissão de administrador.

    - **contrato_id**: ID do contrato
    - **pendencia_id**: ID da pendência a ser cancelada

    Ao cancelar, o fiscal será notificado por email e não precisará mais
    enviar relatório para esta pendência.
    """
    return await service.cancelar_pendencia(contrato_id, pendencia_id, admin_user.id)

@router.get("/contador", summary="Contador de pendências por status")
async def contador_pendencias(
    contrato_id: int,
    service: PendenciaService = Depends(get_pendencia_service),
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
):
    """
    Retorna contador de pendências por status para o dashboard.

    - **contrato_id**: ID do contrato

    Retorna quantidades separadas por status (pendente, análise, concluída, cancelada)
    para exibir badges no frontend como "Pendências(2)".
    """
    # Verificação de permissão
    checker = PermissionChecker(conn)
    if not await checker.can_access_contract(current_user, contrato_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar este contrato"
        )

    return await service.get_contador_pendencias(contrato_id, current_user)