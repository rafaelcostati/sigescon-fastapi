# app/api/routers/arquivo_router.py
import asyncpg
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.dependencies import get_current_user
from app.api.permissions import PermissionChecker
from app.repositories.arquivo_repo import ArquivoRepository

router = APIRouter(
    prefix="/arquivos",
    tags=["Arquivos"]
)

@router.get("/{arquivo_id}/download")
async def download_arquivo(
    arquivo_id: int,
    conn: asyncpg.Connection = Depends(get_connection),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Fornece um arquivo para download.

    Verifica se o usuário logado tem permissão para acessar o contrato
    ao qual o arquivo pertence (seja como admin, gestor ou fiscal).
    """
    arquivo_repo = ArquivoRepository(conn)
    arquivo = await arquivo_repo.find_arquivo_by_id(arquivo_id)

    if not arquivo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado no banco de dados.")

    # Verificação de permissão
    contrato_id = arquivo.get('contrato_id')
    checker = PermissionChecker(conn)
    if not await checker.can_access_contract(current_user, contrato_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para acessar este arquivo.")

    # Verificação de existência física
    path_completo = arquivo.get('path_armazenamento')
    if not os.path.exists(path_completo):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo físico não encontrado no servidor.")

    nome_original = arquivo.get('nome_arquivo')
    
    return FileResponse(
        path=path_completo,
        filename=nome_original,
        media_type=arquivo.get('tipo_arquivo'),
        content_disposition_type="attachment" 
    )