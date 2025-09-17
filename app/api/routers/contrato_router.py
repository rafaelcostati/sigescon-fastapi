# app/api/routers/contrato_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, UploadFile, File, Form
from typing import Optional
from datetime import date

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.dependencies import get_current_user, get_current_admin_user

# Repositórios
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.contratado_repo import ContratadoRepository as ContratadoRepo
from app.repositories.modalidade_repo import ModalidadeRepository
from app.repositories.status_repo import StatusRepository
from app.repositories.arquivo_repo import ArquivoRepository
from app.api.permissions import admin_required, PermissionChecker

# Services
from app.services.contrato_service import ContratoService
from app.services.file_service import FileService

# Schemas
from app.schemas.contrato_schema import (
    Contrato, ContratoCreate, ContratoUpdate, ContratoPaginated
)

router = APIRouter(
    prefix="/contratos",
    tags=["Contratos"]
)

# --- Injeção de Dependências ---
def get_contrato_service(conn: asyncpg.Connection = Depends(get_connection)) -> ContratoService:
    return ContratoService(
        contrato_repo=ContratoRepository(conn),
        usuario_repo=UsuarioRepository(conn),
        contratado_repo=ContratadoRepo(conn),
        modalidade_repo=ModalidadeRepository(conn),
        status_repo=StatusRepository(conn),
        arquivo_repo=ArquivoRepository(conn),
        file_service=FileService()
    )

# --- Endpoints ---

@router.post("/", response_model=Contrato, status_code=status.HTTP_201_CREATED)
async def create_contrato(
    # Declara cada campo do formulário explicitamente
    nr_contrato: str = Form(...),
    objeto: str = Form(...),
    data_inicio: date = Form(...),
    data_fim: date = Form(...),
    contratado_id: int = Form(...),
    modalidade_id: int = Form(...),
    status_id: int = Form(...),
    gestor_id: int = Form(...),
    fiscal_id: int = Form(...),
    valor_anual: Optional[float] = Form(None),
    valor_global: Optional[float] = Form(None),
    base_legal: Optional[str] = Form(None),
    termos_contratuais: Optional[str] = Form(None),
    fiscal_substituto_id: Optional[int] = Form(None),
    pae: Optional[str] = Form(None),
    doe: Optional[str] = Form(None),
    data_doe: Optional[date] = Form(None),
    documento_contrato: Optional[UploadFile] = File(None),
    service: ContratoService = Depends(get_contrato_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Cria um novo contrato. Aceita dados de formulário e um ficheiro opcional.
    Requer permissão de administrador.
    """
    # Constrói manualmente o objeto Pydantic a partir dos campos do formulário
    contrato_create = ContratoCreate(
        nr_contrato=nr_contrato,
        objeto=objeto,
        data_inicio=data_inicio,
        data_fim=data_fim,
        contratado_id=contratado_id,
        modalidade_id=modalidade_id,
        status_id=status_id,
        gestor_id=gestor_id,
        fiscal_id=fiscal_id,
        valor_anual=valor_anual,
        valor_global=valor_global,
        base_legal=base_legal,
        termos_contratuais=termos_contratuais,
        fiscal_substituto_id=fiscal_substituto_id,
        pae=pae,
        doe=doe,
        data_doe=data_doe
    )
    
    return await service.create_contrato(contrato_create, documento_contrato)


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
    filters = {'gestor_id': gestor_id, 'fiscal_id': fiscal_id, 'objeto': objeto, 'nr_contrato': nr_contrato, 'status_id': status_id, 'pae': pae, 'ano': ano}
    active_filters = {k: v for k, v in filters.items() if v is not None}
    return await service.get_all_contratos(page=page, per_page=per_page, filters=active_filters)

@router.get("/{contrato_id}", response_model=Contrato)
async def get_contrato_by_id(
    contrato_id: int, 
    service: ContratoService = Depends(get_contrato_service), 
    current_user: Usuario = Depends(get_current_user),  
    conn: asyncpg.Connection = Depends(get_connection)  
):
    
    from app.api.permissions import PermissionChecker
    
    checker = PermissionChecker(conn)
    if not await checker.can_access_contract(current_user, contrato_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar este contrato"
        )
    
    contrato = await service.get_contrato_by_id(contrato_id)
    if not contrato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
    return contrato

@router.patch("/{contrato_id}", response_model=Contrato)
async def update_contrato(contrato_id: int, contrato_update: ContratoUpdate, service: ContratoService = Depends(get_contrato_service), admin_user: Usuario = Depends(admin_required)):
    updated_contrato = await service.update_contrato(contrato_id, contrato_update)
    if not updated_contrato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado para atualização")
    return updated_contrato

@router.delete("/{contrato_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contrato(contrato_id: int, service: ContratoService = Depends(get_contrato_service), admin_user: Usuario = Depends(admin_required)):
    await service.delete_contrato(contrato_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)