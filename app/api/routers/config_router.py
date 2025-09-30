# app/api/routers/config_router.py
import asyncpg
from fastapi import APIRouter, Depends, status
from typing import List

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.permissions import admin_required
from app.repositories.config_repo import ConfigRepository
from app.services.config_service import ConfigService
from app.schemas.config_schema import Config, ConfigUpdate, PendenciasIntervaloDiasUpdate, LembretesConfigUpdate

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
