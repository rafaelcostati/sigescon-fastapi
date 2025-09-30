# app/api/routers/config_router.py
import asyncpg
from fastapi import APIRouter, Depends, status, File, UploadFile
from fastapi.responses import FileResponse
from typing import List, Optional

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.permissions import admin_required, get_current_user
from app.repositories.config_repo import ConfigRepository
from app.repositories.arquivo_repo import ArquivoRepository
from app.services.config_service import ConfigService
from app.services.file_service import FileService
from app.schemas.config_schema import Config, ConfigUpdate, PendenciasIntervaloDiasUpdate, LembretesConfigUpdate, ModeloRelatorioInfo, ModeloRelatorioResponse

router = APIRouter(
    prefix="/config",
    tags=["Configurações"]
)

# --- Injeção de Dependências ---
def get_config_service(conn: asyncpg.Connection = Depends(get_connection)) -> ConfigService:
    return ConfigService(
        config_repo=ConfigRepository(conn)
    )

# --- Endpoints ---

@router.get("/", response_model=List[Config], summary="Listar todas as configurações")
async def list_configs(
    service: ConfigService = Depends(get_config_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Lista todas as configurações do sistema.
    Requer permissão de administrador.
    """
    return await service.get_all_configs()


@router.get("/{chave}", response_model=Config, summary="Buscar configuração por chave")
async def get_config(
    chave: str,
    service: ConfigService = Depends(get_config_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Busca uma configuração específica pela chave.
    Requer permissão de administrador.
    """
    return await service.get_config(chave)


@router.patch("/{chave}", response_model=Config, summary="Atualizar configuração")
async def update_config(
    chave: str,
    config_update: ConfigUpdate,
    service: ConfigService = Depends(get_config_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Atualiza o valor de uma configuração.
    Requer permissão de administrador.
    """
    return await service.update_config(chave, config_update)


@router.get("/pendencias/intervalo-dias", response_model=dict, summary="Obter intervalo de dias para pendências")
async def get_pendencias_intervalo_dias(
    service: ConfigService = Depends(get_config_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Retorna o intervalo de dias configurado para criação automática de pendências.
    Requer permissão de administrador.
    """
    intervalo = await service.get_pendencias_intervalo_dias()
    return {"intervalo_dias": intervalo}


@router.patch("/pendencias/intervalo-dias", response_model=Config, summary="Atualizar intervalo de dias")
async def update_pendencias_intervalo_dias(
    update_data: PendenciasIntervaloDiasUpdate,
    service: ConfigService = Depends(get_config_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Atualiza o intervalo de dias para criação automática de pendências.
    Requer permissão de administrador.

    - **intervalo_dias**: Número de dias entre cada pendência automática (1-365)
    """
    return await service.update_pendencias_intervalo_dias(update_data.intervalo_dias)


@router.get("/lembretes/config", response_model=dict, summary="Obter configurações de lembretes")
async def get_lembretes_config(
    service: ConfigService = Depends(get_config_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Retorna as configurações de lembretes de pendências.
    Requer permissão de administrador.
    
    Retorna:
    - **dias_antes_vencimento_inicio**: Quantos dias antes do vencimento começar a enviar lembretes
    - **intervalo_dias_lembrete**: A cada quantos dias enviar lembretes até o vencimento
    """
    return await service.get_lembretes_config()


@router.patch("/lembretes/config", response_model=dict, summary="Atualizar configurações de lembretes")
async def update_lembretes_config(
    update_data: LembretesConfigUpdate,
    service: ConfigService = Depends(get_config_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Atualiza as configurações de lembretes de pendências.
    Requer permissão de administrador.
    
    - **dias_antes_vencimento_inicio**: Quantos dias antes do vencimento começar a enviar (1-90)
    - **intervalo_dias_lembrete**: A cada quantos dias enviar lembretes (1-30)
    
    Exemplo: dias_antes_vencimento_inicio=30 e intervalo_dias_lembrete=5
    Resultado: Lembretes serão enviados 30, 25, 20, 15, 10, 5 dias antes e no dia do vencimento.
    """
    return await service.update_lembretes_config(
        update_data.dias_antes_vencimento_inicio,
        update_data.intervalo_dias_lembrete
    )


# ==================== Modelo de Relatório ====================

@router.get("/modelo-relatorio/info", response_model=Optional[ModeloRelatorioInfo], summary="Obter informações do modelo de relatório")
async def get_modelo_relatorio_info(
    service: ConfigService = Depends(get_config_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna informações sobre o modelo de relatório ativo.
    Disponível para todos os usuários autenticados.
    
    Retorna:
    - **arquivo_id**: ID do arquivo no sistema
    - **nome_original**: Nome original do arquivo
    - **ativo**: Se o modelo está ativo
    
    Retorna None se não houver modelo configurado.
    """
    return await service.get_modelo_relatorio_info()


@router.post("/modelo-relatorio/upload", response_model=ModeloRelatorioResponse, summary="Fazer upload do modelo de relatório")
async def upload_modelo_relatorio(
    file: UploadFile = File(...),
    conn: asyncpg.Connection = Depends(get_connection),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Faz upload de um novo modelo de relatório.
    Se já existir um modelo, substitui o anterior.
    Requer permissão de administrador.
    
    - **file**: Arquivo do modelo (PDF, DOC, DOCX, ODT)
    
    O modelo de relatório será disponibilizado para download em todos os contratos.
    """
    config_service = ConfigService(config_repo=ConfigRepository(conn))
    arquivo_repo = ArquivoRepository(conn)
    file_service = FileService()
    
    return await config_service.upload_modelo_relatorio(file, arquivo_repo, file_service)


@router.delete("/modelo-relatorio", response_model=ModeloRelatorioResponse, summary="Remover modelo de relatório")
async def remove_modelo_relatorio(
    conn: asyncpg.Connection = Depends(get_connection),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Remove o modelo de relatório ativo.
    Requer permissão de administrador.
    
    O arquivo será deletado do sistema de arquivos e do banco de dados.
    """
    config_service = ConfigService(config_repo=ConfigRepository(conn))
    arquivo_repo = ArquivoRepository(conn)
    
    return await config_service.remove_modelo_relatorio(arquivo_repo)


@router.get("/modelo-relatorio/download", summary="Fazer download do modelo de relatório")
async def download_modelo_relatorio(
    conn: asyncpg.Connection = Depends(get_connection),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Faz download do modelo de relatório ativo.
    Disponível para todos os usuários autenticados.
    
    Retorna o arquivo para download.
    """
    config_repo = ConfigRepository(conn)
    arquivo_repo = ArquivoRepository(conn)
    
    # Busca informações do modelo
    modelo_info = await config_repo.get_modelo_relatorio_info()
    if not modelo_info:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum modelo de relatório configurado"
        )
    
    # Busca informações do arquivo
    arquivo = await arquivo_repo.get_arquivo_by_id(modelo_info['arquivo_id'])
    if not arquivo:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo do modelo não encontrado"
        )
    
    # Retorna o arquivo
    return FileResponse(
        path=arquivo['caminho'],
        filename=arquivo['nome_original'],
        media_type='application/octet-stream'
    )
