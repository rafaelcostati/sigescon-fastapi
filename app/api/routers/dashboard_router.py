# app/api/routers/dashboard_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.dependencies import get_current_user, get_current_fiscal_user
from app.api.permissions import admin_required, require_admin_or_fiscal
from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository

# Repositórios e Serviços
from app.repositories.dashboard_repo import DashboardRepository
from app.services.dashboard_service import DashboardService

# Schemas
from app.schemas.dashboard_schema import (
    ContratosComPendencias,
    ContratosComRelatoriosPendentes,
    MinhasPendenciasResponse,
    ContadoresDashboard,
    DashboardAdminResponse,
    DashboardFiscalResponse,
    PendenciasVencidasAdminResponse
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


# --- Injeção de Dependências ---
def get_dashboard_service(conn: asyncpg.Connection = Depends(get_connection)) -> DashboardService:
    return DashboardService(
        dashboard_repo=DashboardRepository(conn)
    )


# --- Endpoints Para Administrador ---

@router.get("/admin/contratos-com-relatorios-pendentes", response_model=ContratosComRelatoriosPendentes)
async def get_contratos_relatorios_pendentes(
    limit: int = Query(20, ge=1, le=100, description="Limite de contratos retornados"),
    service: DashboardService = Depends(get_dashboard_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Lista contratos que têm relatórios aguardando análise pelo administrador.

    - **limit**: Número máximo de contratos a retornar (padrão: 20, máximo: 100)

    Retorna contratos ordenados pela data do relatório mais antigo aguardando análise.
    Útil para priorizar análises por ordem de chegada.
    """
    return await service.get_contratos_com_relatorios_pendentes(limit)


@router.get("/admin/contratos-com-pendencias", response_model=ContratosComPendencias)
async def get_contratos_com_pendencias(
    limit: int = Query(20, ge=1, le=100, description="Limite de contratos retornados"),
    service: DashboardService = Depends(get_dashboard_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Lista contratos que têm pendências ativas (status 'Pendente').

    - **limit**: Número máximo de contratos a retornar (padrão: 20, máximo: 100)

    Retorna contratos ordenados pela data da pendência mais antiga.
    Inclui contador de pendências em atraso por contrato.
    """
    return await service.get_contratos_com_pendencias(limit)


@router.get("/admin/completo", response_model=DashboardAdminResponse)
async def get_dashboard_admin_completo(
    service: DashboardService = Depends(get_dashboard_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Retorna dados completos para o dashboard do administrador.

    Inclui:
    - Contadores gerais (relatórios, pendências, usuários, contratos)
    - Top 10 contratos com relatórios pendentes
    - Top 10 contratos com pendências ativas

    Endpoint otimizado para carregar todo o dashboard administrativo de uma vez.
    """
    return await service.get_dashboard_admin_completo()


@router.get("/admin/pendencias-vencidas", response_model=PendenciasVencidasAdminResponse)
async def get_pendencias_vencidas_admin(
    limit: int = Query(50, ge=1, le=200, description="Limite de pendências retornadas"),
    service: DashboardService = Depends(get_dashboard_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Lista todas as pendências vencidas do sistema com informações detalhadas.

    - **limit**: Número máximo de pendências a retornar (padrão: 50, máximo: 200)

    Retorna pendências ordenadas por urgência:
    - **CRÍTICAS** (>30 dias): Aparecem primeiro
    - **ALTAS** (15-30 dias): Segundo lugar
    - **MÉDIAS** (1-14 dias): Por último

    Dentro de cada nível, ordena pelos mais atrasados primeiro.

    **Informações incluídas:**
    - Detalhes da pendência (título, descrição, prazo)
    - Dias em atraso e classificação de urgência
    - Dados do contrato (número, objeto)
    - Responsáveis (fiscal e gestor)
    - Estatísticas de urgência

    **Ideal para:**
    - Identificar pendências críticas que precisam ação imediata
    - Cobrar fiscais com pendências em atraso
    - Relatórios de acompanhamento para gestão
    """
    return await service.get_pendencias_vencidas_admin(limit)


# --- Endpoints Para Fiscal ---

@router.get("/fiscal/minhas-pendencias", response_model=MinhasPendenciasResponse)
async def get_minhas_pendencias(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: Usuario = Depends(get_current_fiscal_user)
):
    """
    Lista todas as pendências ativas do fiscal logado.

    Retorna pendências ordenadas por prioridade:
    1. Pendências em atraso
    2. Pendências por prazo de entrega
    3. Pendências por data de criação

    Inclui informações de contrato e contadores de atraso.
    Disponível para usuários com perfil de Fiscal ou Administrador.
    """
    return await service.get_minhas_pendencias_fiscal(current_user.id)


@router.get("/fiscal/completo", response_model=DashboardFiscalResponse)
async def get_dashboard_fiscal_completo(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: Usuario = Depends(get_current_fiscal_user)
):
    """
    Retorna dados completos para o dashboard do fiscal.

    Inclui:
    - Contadores específicos do fiscal (pendências, relatórios enviados)
    - Lista completa de pendências ativas

    Endpoint otimizado para carregar todo o dashboard do fiscal de uma vez.
    Disponível para usuários com perfil de Fiscal ou Administrador.
    """
    return await service.get_dashboard_fiscal_completo(current_user.id)


# --- Endpoint Geral de Contadores ---

@router.get("/contadores", response_model=ContadoresDashboard)
async def get_contadores_dashboard(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna contadores para dashboard baseado no perfil ativo do usuário.

    - **Administrador**: Relatórios para análise, contratos com pendências, usuários e contratos ativos
    - **Fiscal**: Pendências pessoais, em atraso e relatórios enviados no mês
    - **Gestor**: Contratos sob gestão e relatórios da equipe pendentes

    Os contadores são cumulativos caso o usuário tenha múltiplos perfis.
    Útil para exibir badges no frontend como "Pendências(3)" ou "Relatórios(5)".
    """
    return await service.get_contadores_dashboard(current_user)


# --- Endpoints de Conveniência ---

@router.get("/resumo-atividades")
async def get_resumo_atividades(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
):
    """
    Endpoint de conveniência que retorna um resumo das atividades baseado no perfil do usuário.

    Retorna diferentes dados dependendo dos perfis do usuário:
    - **Administrador**: Contratos com ação necessária
    - **Fiscal**: Pendências pessoais urgentes
    - **Gestor**: Status dos contratos sob gestão

    Ideal para notificações e alertas no frontend.
    """
    # Verificar perfis do usuário usando o sistema de múltiplos perfis
    usuario_perfil_repo = UsuarioPerfilRepository(conn)

    is_admin = await usuario_perfil_repo.has_profile(current_user.id, "Administrador")
    is_fiscal = await usuario_perfil_repo.has_profile(current_user.id, "Fiscal")
    is_gestor = await usuario_perfil_repo.has_profile(current_user.id, "Gestor")

    # Prioridade: Admin > Fiscal > Gestor
    if is_admin:
        # Para admin: contratos que precisam de ação
        relatorios_pendentes = await service.get_contratos_com_relatorios_pendentes(5)
        contratos_pendencias = await service.get_contratos_com_pendencias(5)

        return {
            "perfil": "Administrador",
            "relatorios_para_analisar": len(relatorios_pendentes.contratos),
            "contratos_com_pendencias": len(contratos_pendencias.contratos),
            "acao_necessaria": relatorios_pendentes.total_relatorios_pendentes > 0 or contratos_pendencias.total_pendencias > 0
        }

    elif is_fiscal:
        # Para fiscal: suas pendências urgentes
        minhas_pendencias = await service.get_minhas_pendencias_fiscal(current_user.id)

        return {
            "perfil": "Fiscal",
            "total_pendencias": minhas_pendencias.total_pendencias,
            "pendencias_em_atraso": minhas_pendencias.pendencias_em_atraso,
            "pendencias_proximas_vencimento": minhas_pendencias.pendencias_proximas_vencimento,
            "acao_necessaria": minhas_pendencias.total_pendencias > 0
        }

    elif is_gestor:
        # Para gestores
        contadores = await service.get_contadores_dashboard(current_user)

        return {
            "perfil": "Gestor",
            "contratos_sob_gestao": contadores.contratos_sob_gestao,
            "relatorios_equipe_pendentes": contadores.relatorios_equipe_pendentes,
            "acao_necessaria": contadores.relatorios_equipe_pendentes > 0
        }

    else:
        # Para usuários sem perfis específicos
        return {
            "perfil": "Outros",
            "acao_necessaria": False,
            "mensagem": "Nenhum perfil ativo encontrado"
        }