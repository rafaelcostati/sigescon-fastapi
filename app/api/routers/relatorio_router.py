# app/api/routers/relatorio_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List
from datetime import date

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.dependencies import get_current_user, get_current_admin_user
from app.api.permissions import admin_required, require_contract_access

# Repositórios
from app.repositories.relatorio_repo import RelatorioRepository
from app.repositories.arquivo_repo import ArquivoRepository
from app.repositories.pendencia_repo import PendenciaRepository
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.status_relatorio_repo import StatusRelatorioRepository
from app.repositories.status_pendencia_repo import StatusPendenciaRepository
from app.repositories.usuario_repo import UsuarioRepository

# Services
from app.services.relatorio_service import RelatorioService
from app.services.file_service import FileService

# Schemas
from app.schemas.relatorio_schema import Relatorio, RelatorioCreate, RelatorioAnalise

router = APIRouter(
    prefix="/contratos/{contrato_id}/relatorios",
    tags=["Relatórios Fiscais"]
)

# --- Injeção de Dependências ---
def get_relatorio_service(conn: asyncpg.Connection = Depends(get_connection)) -> RelatorioService:
    return RelatorioService(
        relatorio_repo=RelatorioRepository(conn),
        arquivo_repo=ArquivoRepository(conn),
        pendencia_repo=PendenciaRepository(conn),
        contrato_repo=ContratoRepository(conn),
        status_relatorio_repo=StatusRelatorioRepository(conn),
        status_pendencia_repo=StatusPendenciaRepository(conn),
        usuario_repo=UsuarioRepository(conn),
        file_service=FileService()
    )

# --- Endpoints ---

@router.post("/", response_model=Relatorio, status_code=status.HTTP_201_CREATED)
async def submit_relatorio(
    contrato_id: int,
    arquivo: UploadFile = File(...),
    mes_competencia: date = Form(...),
    observacoes_fiscal: str | None = Form(None),
    pendencia_id: int = Form(...),
    service: RelatorioService = Depends(get_relatorio_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Submete um novo relatório fiscal para um contrato, respondendo a uma pendência."""
    relatorio_data = RelatorioCreate(
        mes_competencia=mes_competencia,
        observacoes_fiscal=observacoes_fiscal,
        pendencia_id=pendencia_id,
        fiscal_usuario_id=current_user.id
    )
    return await service.submit_relatorio(contrato_id, relatorio_data, arquivo, current_user)


@router.get("/", response_model=List[Relatorio])
async def list_relatorios(
    contrato_id: int,
    service: RelatorioService = Depends(get_relatorio_service),
    current_user: Usuario = Depends(require_contract_access)
):
    """Lista todos os relatórios de um contrato específico."""
    return await service.get_relatorios_by_contrato_id(contrato_id)


@router.patch("/{relatorio_id}/analise", response_model=Relatorio)
async def analisar_relatorio(
    contrato_id: int,
    relatorio_id: int,
    analise_data: RelatorioAnalise,
    service: RelatorioService = Depends(get_relatorio_service),
    admin_user: Usuario = Depends(admin_required)
):
    """Aprova ou rejeita um relatório. Requer permissão de administrador."""
    return await service.analisar_relatorio(relatorio_id, analise_data)