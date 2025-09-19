# app/api/routers/contrato_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List, Optional
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
    Contrato, ContratoCreate, ContratoUpdate, ContratoPaginated, ArquivoContrato, ArquivoContratoList
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
    documento_contrato: List[UploadFile] = File(None),
    service: ContratoService = Depends(get_contrato_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Cria um novo contrato. Aceita dados de formulário e múltiplos ficheiros opcionais.
    Requer permissão de administrador.

    Limites de upload:
    - Máximo 10 arquivos por upload
    - 100MB por arquivo individual
    - 250MB total
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
async def update_contrato(
    contrato_id: int,
    # Campos opcionais do formulário - apenas os campos que podem ser atualizados
    nr_contrato: Optional[str] = Form(None),
    objeto: Optional[str] = Form(None),
    data_inicio: Optional[date] = Form(None),
    data_fim: Optional[date] = Form(None),
    contratado_id: Optional[int] = Form(None),
    modalidade_id: Optional[int] = Form(None),
    status_id: Optional[int] = Form(None),
    gestor_id: Optional[int] = Form(None),
    fiscal_id: Optional[int] = Form(None),
    valor_anual: Optional[float] = Form(None),
    valor_global: Optional[float] = Form(None),
    base_legal: Optional[str] = Form(None),
    termos_contratuais: Optional[str] = Form(None),
    fiscal_substituto_id: Optional[int] = Form(None),
    pae: Optional[str] = Form(None),
    doe: Optional[str] = Form(None),
    data_doe: Optional[date] = Form(None),
    # Arquivos opcionais para upload
    documento_contrato: List[UploadFile] = File(None),
    service: ContratoService = Depends(get_contrato_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Atualiza um contrato existente. Aceita dados de formulário e múltiplos ficheiros opcionais.
    Requer permissão de administrador.

    - **contrato_id**: ID do contrato a ser atualizado
    - **nr_contrato**: Número do contrato (pode ser alterado)
    - **documento_contrato**: Arquivos opcionais para adicionar ao contrato
    - **outros campos**: Campos opcionais do contrato para atualização

    Limites de upload:
    - Máximo 10 arquivos por upload
    - 100MB por arquivo individual
    - 250MB total

    Todos os campos são opcionais - apenas os fornecidos serão atualizados.
    **ATENÇÃO**: Alterar o número do contrato pode impactar relatórios e histórico.
    """
    
    # Constrói objeto ContratoUpdate apenas com campos fornecidos
    update_data = {}
    
    # Lista todos os campos que podem ser atualizados
    form_fields = {
        'nr_contrato': nr_contrato,
        'objeto': objeto,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'contratado_id': contratado_id,
        'modalidade_id': modalidade_id,
        'status_id': status_id,
        'gestor_id': gestor_id,
        'fiscal_id': fiscal_id,
        'valor_anual': valor_anual,
        'valor_global': valor_global,
        'base_legal': base_legal,
        'termos_contratuais': termos_contratuais,
        'fiscal_substituto_id': fiscal_substituto_id,
        'pae': pae,
        'doe': doe,
        'data_doe': data_doe
    }
    
    # Inclui apenas campos não None no update
    for field, value in form_fields.items():
        if value is not None:
            update_data[field] = value
    
    # Cria o schema de update
    contrato_update = ContratoUpdate(**update_data)
    
    # Chama o service passando o arquivo se fornecido
    updated_contrato = await service.update_contrato(
        contrato_id=contrato_id, 
        contrato_update=contrato_update, 
        documento_contrato=documento_contrato
    )
    
    if not updated_contrato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Contrato não encontrado para atualização"
        )
    
    return updated_contrato

@router.delete("/{contrato_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contrato(contrato_id: int, service: ContratoService = Depends(get_contrato_service), admin_user: Usuario = Depends(admin_required)):
    await service.delete_contrato(contrato_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Rotas para gerenciamento de arquivos do contrato
@router.get("/{contrato_id}/arquivos", response_model=ArquivoContratoList, summary="Listar arquivos do contrato")
async def listar_arquivos_contrato(
    contrato_id: int,
    service: ContratoService = Depends(get_contrato_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos os arquivos de um contrato específico.

    - **contrato_id**: ID do contrato

    Retorna uma lista com todos os arquivos associados ao contrato,
    incluindo informações como nome, tipo, tamanho e data de criação.
    """
    return await service.get_arquivos_contrato(contrato_id)

@router.get("/{contrato_id}/arquivos/{arquivo_id}/download", summary="Download de arquivo do contrato")
async def download_arquivo_contrato(
    contrato_id: int,
    arquivo_id: int,
    service: ContratoService = Depends(get_contrato_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Download de um arquivo específico de um contrato.

    - **contrato_id**: ID do contrato
    - **arquivo_id**: ID do arquivo a ser baixado

    Retorna o arquivo para download com o nome original e tipo MIME correto.
    """
    arquivo = await service.get_arquivo_contrato(contrato_id, arquivo_id)

    # Verificação de existência física do arquivo
    import os
    path_completo = arquivo['path_armazenamento']
    if not os.path.exists(path_completo):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico não encontrado no servidor"
        )

    nome_original = arquivo['nome_arquivo']

    return FileResponse(
        path=path_completo,
        filename=nome_original,
        media_type='application/octet-stream'
    )

@router.delete("/{contrato_id}/arquivos/{arquivo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir arquivo do contrato")
async def excluir_arquivo_contrato(
    contrato_id: int,
    arquivo_id: int,
    service: ContratoService = Depends(get_contrato_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Remove um arquivo específico de um contrato.

    - **contrato_id**: ID do contrato
    - **arquivo_id**: ID do arquivo a ser removido

    **Atenção**: Esta operação remove permanentemente o arquivo tanto do banco
    de dados quanto do sistema de arquivos. Requer permissão de administrador.
    """
    await service.delete_arquivo_contrato(contrato_id, arquivo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)