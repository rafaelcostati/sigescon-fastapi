"""
Router para logs de auditoria
"""
import asyncpg
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.permissions import admin_required, get_current_user
from app.repositories.audit_log_repo import AuditLogRepository
from app.services.audit_log_service import AuditLogService
from app.schemas.audit_log_schema import (
    AuditLog,
    AuditLogList,
    AuditLogFilter,
    AuditStatistics,
    AcaoAuditoria,
    EntidadeAuditoria
)


router = APIRouter(
    prefix="/audit-logs",
    tags=["Auditoria"]
)


# ==================== Dependency Injection ====================

def get_audit_service(conn: asyncpg.Connection = Depends(get_connection)) -> AuditLogService:
    """Injeta o serviço de auditoria"""
    return AuditLogService(audit_repo=AuditLogRepository(conn))


# ==================== Endpoints ====================

@router.get("/", response_model=AuditLogList, summary="Listar logs de auditoria")
async def listar_logs(
    # Filtros
    usuario_id: Optional[int] = Query(None, description="Filtrar por usuário"),
    perfil: Optional[str] = Query(None, description="Filtrar por perfil"),
    acao: Optional[AcaoAuditoria] = Query(None, description="Filtrar por ação"),
    entidade: Optional[EntidadeAuditoria] = Query(None, description="Filtrar por entidade"),
    entidade_id: Optional[int] = Query(None, description="Filtrar por ID da entidade"),
    data_inicio: Optional[datetime] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[datetime] = Query(None, description="Data final (YYYY-MM-DD)"),
    busca: Optional[str] = Query(None, description="Buscar na descrição"),

    # Paginação
    pagina: int = Query(1, ge=1, description="Número da página"),
    tamanho_pagina: int = Query(50, ge=1, le=100, description="Itens por página"),

    # Ordenação
    ordenar_por: str = Query("data_hora", description="Campo para ordenar"),
    ordem: str = Query("DESC", description="ASC ou DESC"),

    # Deps
    service: AuditLogService = Depends(get_audit_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Lista todos os logs de auditoria com filtros e paginação.

    **Apenas administradores** podem acessar os logs de auditoria.

    **Filtros disponíveis:**
    - **usuario_id**: ID do usuário que realizou a ação
    - **perfil**: Perfil ativo (Administrador, Gestor, Fiscal)
    - **acao**: Tipo de ação (CRIAR, ATUALIZAR, DELETAR, etc)
    - **entidade**: Tipo de entidade (CONTRATO, PENDENCIA, RELATORIO, etc)
    - **entidade_id**: ID específico da entidade
    - **data_inicio** e **data_fim**: Período de busca
    - **busca**: Busca texto livre na descrição

    **Ordenação:**
    - Campos: id, data_hora, usuario_nome, acao, entidade
    - Ordem: ASC ou DESC
    """
    filters = AuditLogFilter(
        usuario_id=usuario_id,
        perfil=perfil,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        busca=busca,
        pagina=pagina,
        tamanho_pagina=tamanho_pagina,
        ordenar_por=ordenar_por,
        ordem=ordem
    )

    return await service.listar_logs(filters)


@router.get("/statistics", response_model=AuditStatistics, summary="Estatísticas de auditoria")
async def obter_estatisticas(
    service: AuditLogService = Depends(get_audit_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Obtém estatísticas gerais dos logs de auditoria.

    **Apenas administradores**.

    **Retorna:**
    - Total de logs
    - Logs por ação (distribuição)
    - Logs por entidade (distribuição)
    - Top 10 usuários mais ativos
    - Logs nas últimas 24 horas
    - Logs na última semana
    """
    return await service.obter_estatisticas()


@router.get("/{log_id}", response_model=AuditLog, summary="Buscar log específico")
async def buscar_log(
    log_id: int,
    service: AuditLogService = Depends(get_audit_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Busca um log específico por ID.

    **Apenas administradores**.
    """
    log = await service.buscar_log_por_id(log_id)
    if not log:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log não encontrado"
        )
    return log


@router.get("/entidade/{entidade}/{entidade_id}", response_model=list[AuditLog], summary="Logs de uma entidade")
async def listar_logs_por_entidade(
    entidade: EntidadeAuditoria,
    entidade_id: int,
    limit: int = Query(50, ge=1, le=200, description="Limite de resultados"),
    service: AuditLogService = Depends(get_audit_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos os logs relacionados a uma entidade específica.

    **Exemplo:** Ver histórico de alterações de um contrato específico

    **Parâmetros:**
    - **entidade**: Tipo (CONTRATO, PENDENCIA, RELATORIO, etc)
    - **entidade_id**: ID da entidade
    - **limit**: Número máximo de logs (padrão: 50, máx: 200)

    **Permissões:**
    - Administradores: podem ver logs de qualquer entidade
    - Outros usuários: podem ver logs de entidades relacionadas a eles
    """
    return await service.listar_logs_por_entidade(entidade, entidade_id, limit)


@router.get("/usuario/{usuario_id}", response_model=list[AuditLog], summary="Logs de um usuário")
async def listar_logs_por_usuario(
    usuario_id: int,
    limit: int = Query(100, ge=1, le=500, description="Limite de resultados"),
    service: AuditLogService = Depends(get_audit_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos os logs de um usuário específico.

    **Permissões:**
    - Usuários podem ver seus próprios logs
    - Administradores podem ver logs de qualquer usuário
    """
    # Verificar permissão
    if current_user.id != usuario_id and not any(p.nome == "Administrador" for p in current_user.perfis):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para ver logs de outros usuários"
        )

    return await service.listar_logs_por_usuario(usuario_id, limit)


@router.delete("/cleanup", summary="Limpar logs antigos")
async def limpar_logs_antigos(
    dias_retencao: int = Query(365, ge=30, le=3650, description="Dias para manter logs"),
    service: AuditLogService = Depends(get_audit_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Remove logs de auditoria mais antigos que X dias.

    **Apenas administradores**.

    **Retenção padrão:** 365 dias (1 ano)
    **Mínimo:** 30 dias
    **Máximo:** 3650 dias (10 anos)

    **⚠️ ATENÇÃO:** Esta ação é irreversível!
    """
    registros_deletados = await service.limpar_logs_antigos(dias_retencao)

    return {
        "message": f"Limpeza concluída com sucesso",
        "registros_deletados": registros_deletados,
        "dias_retencao": dias_retencao
    }
