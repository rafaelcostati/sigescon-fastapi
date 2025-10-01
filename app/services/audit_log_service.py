"""
Service para logs de auditoria
"""
from typing import Optional, Dict, Any
from fastapi import Request
from app.repositories.audit_log_repo import AuditLogRepository
from app.schemas.audit_log_schema import (
    AuditLogCreate,
    AuditLogFilter,
    AuditLogList,
    AuditLog,
    AuditStatistics,
    AcaoAuditoria,
    EntidadeAuditoria
)
from app.schemas.usuario_schema import Usuario


class AuditLogService:
    """Service para gerenciar logs de auditoria"""

    def __init__(self, audit_repo: AuditLogRepository):
        self.audit_repo = audit_repo

    async def criar_log(
        self,
        usuario: Usuario,
        acao: AcaoAuditoria,
        entidade: EntidadeAuditoria,
        descricao: str,
        entidade_id: Optional[int] = None,
        dados_anteriores: Optional[Dict[str, Any]] = None,
        dados_novos: Optional[Dict[str, Any]] = None,
        perfil_usado: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo log de auditoria

        Args:
            usuario: Usuário que realizou a ação
            acao: Tipo de ação
            entidade: Tipo de entidade
            descricao: Descrição da ação
            entidade_id: ID da entidade (opcional)
            dados_anteriores: Estado anterior (opcional)
            dados_novos: Estado novo (opcional)
            perfil_usado: Perfil ativo (opcional)
            ip_address: IP do cliente (opcional)
            user_agent: User agent (opcional)

        Returns:
            Log criado
        """
        log_data = AuditLogCreate(
            usuario_id=usuario.id,
            usuario_nome=usuario.nome,
            perfil_usado=perfil_usado,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            descricao=descricao,
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return await self.audit_repo.create_log(log_data)

    async def criar_log_from_request(
        self,
        request: Request,
        usuario: Usuario,
        acao: AcaoAuditoria,
        entidade: EntidadeAuditoria,
        descricao: str,
        entidade_id: Optional[int] = None,
        dados_anteriores: Optional[Dict[str, Any]] = None,
        dados_novos: Optional[Dict[str, Any]] = None,
        perfil_usado: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria log extraindo informações do request

        Args:
            request: Request FastAPI
            usuario: Usuário que realizou a ação
            acao: Tipo de ação
            entidade: Tipo de entidade
            descricao: Descrição da ação
            entidade_id: ID da entidade (opcional)
            dados_anteriores: Estado anterior (opcional)
            dados_novos: Estado novo (opcional)
            perfil_usado: Perfil ativo (opcional)

        Returns:
            Log criado
        """
        # Extrair IP do cliente
        ip_address = request.client.host if request.client else None

        # Extrair user agent
        user_agent = request.headers.get("user-agent")

        return await self.criar_log(
            usuario=usuario,
            acao=acao,
            entidade=entidade,
            descricao=descricao,
            entidade_id=entidade_id,
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            perfil_usado=perfil_usado,
            ip_address=ip_address,
            user_agent=user_agent
        )

    async def listar_logs(self, filters: AuditLogFilter) -> AuditLogList:
        """
        Lista logs com filtros e paginação

        Args:
            filters: Filtros de busca

        Returns:
            Lista paginada de logs
        """
        logs, total = await self.audit_repo.get_logs_with_filters(filters)

        # Calcular total de páginas
        total_paginas = (total + filters.tamanho_pagina - 1) // filters.tamanho_pagina

        return AuditLogList(
            logs=[AuditLog(**log) for log in logs],
            total=total,
            pagina=filters.pagina,
            tamanho_pagina=filters.tamanho_pagina,
            total_paginas=total_paginas
        )

    async def buscar_log_por_id(self, log_id: int) -> Optional[AuditLog]:
        """
        Busca um log específico

        Args:
            log_id: ID do log

        Returns:
            Log ou None
        """
        log = await self.audit_repo.get_log_by_id(log_id)
        return AuditLog(**log) if log else None

    async def listar_logs_por_entidade(
        self,
        entidade: EntidadeAuditoria,
        entidade_id: int,
        limit: int = 50
    ) -> list[AuditLog]:
        """
        Lista logs de uma entidade específica

        Args:
            entidade: Tipo da entidade
            entidade_id: ID da entidade
            limit: Limite de resultados

        Returns:
            Lista de logs
        """
        logs = await self.audit_repo.get_logs_by_entidade(
            entidade=entidade.value,
            entidade_id=entidade_id,
            limit=limit
        )
        return [AuditLog(**log) for log in logs]

    async def listar_logs_por_usuario(
        self,
        usuario_id: int,
        limit: int = 100
    ) -> list[AuditLog]:
        """
        Lista logs de um usuário

        Args:
            usuario_id: ID do usuário
            limit: Limite de resultados

        Returns:
            Lista de logs
        """
        logs = await self.audit_repo.get_logs_by_usuario(usuario_id, limit)
        return [AuditLog(**log) for log in logs]

    async def obter_estatisticas(self) -> AuditStatistics:
        """
        Obtém estatísticas de auditoria

        Returns:
            Estatísticas
        """
        stats = await self.audit_repo.get_statistics()
        return AuditStatistics(**stats)

    async def limpar_logs_antigos(self, dias_retencao: int = 365) -> int:
        """
        Remove logs antigos

        Args:
            dias_retencao: Dias para manter

        Returns:
            Número de registros removidos
        """
        return await self.audit_repo.delete_old_logs(dias_retencao)


# ==================== Funções Helper para Logs Específicos ====================

async def log_criar_contrato(
    service: AuditLogService,
    request: Request,
    usuario: Usuario,
    contrato_id: int,
    dados_contrato: Dict[str, Any],
    perfil_usado: Optional[str] = None
):
    """Helper para logar criação de contrato"""
    return await service.criar_log_from_request(
        request=request,
        usuario=usuario,
        acao=AcaoAuditoria.CRIAR,
        entidade=EntidadeAuditoria.CONTRATO,
        entidade_id=contrato_id,
        descricao=f"Criou o contrato #{dados_contrato.get('nr_contrato', contrato_id)}",
        dados_novos=dados_contrato,
        perfil_usado=perfil_usado
    )


async def log_atualizar_contrato(
    service: AuditLogService,
    request: Request,
    usuario: Usuario,
    contrato_id: int,
    nr_contrato: str,
    dados_anteriores: Dict[str, Any],
    dados_novos: Dict[str, Any],
    perfil_usado: Optional[str] = None
):
    """Helper para logar atualização de contrato"""
    # Identificar campos alterados
    campos_alterados = []
    for key in dados_novos:
        if key in dados_anteriores and dados_anteriores[key] != dados_novos[key]:
            campos_alterados.append(key)

    descricao = f"Atualizou o contrato #{nr_contrato}"
    if campos_alterados:
        descricao += f" (campos: {', '.join(campos_alterados)})"

    return await service.criar_log_from_request(
        request=request,
        usuario=usuario,
        acao=AcaoAuditoria.ATUALIZAR,
        entidade=EntidadeAuditoria.CONTRATO,
        entidade_id=contrato_id,
        descricao=descricao,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        perfil_usado=perfil_usado
    )


async def log_criar_pendencia(
    service: AuditLogService,
    request: Request,
    usuario: Usuario,
    pendencia_id: int,
    titulo_pendencia: str,
    contrato_nr: str,
    perfil_usado: Optional[str] = None
):
    """Helper para logar criação de pendência"""
    return await service.criar_log_from_request(
        request=request,
        usuario=usuario,
        acao=AcaoAuditoria.CRIAR,
        entidade=EntidadeAuditoria.PENDENCIA,
        entidade_id=pendencia_id,
        descricao=f"Criou a pendência '{titulo_pendencia}' no contrato #{contrato_nr}",
        perfil_usado=perfil_usado
    )


async def log_avaliar_pendencia(
    service: AuditLogService,
    request: Request,
    usuario: Usuario,
    pendencia_id: int,
    titulo_pendencia: str,
    status_anterior: str,
    status_novo: str,
    perfil_usado: Optional[str] = None
):
    """Helper para logar avaliação de pendência"""
    acao = AcaoAuditoria.CONCLUIR if status_novo == "Concluída" else AcaoAuditoria.ATUALIZAR

    return await service.criar_log_from_request(
        request=request,
        usuario=usuario,
        acao=acao,
        entidade=EntidadeAuditoria.PENDENCIA,
        entidade_id=pendencia_id,
        descricao=f"Alterou status da pendência '{titulo_pendencia}' de '{status_anterior}' para '{status_novo}'",
        dados_anteriores={"status": status_anterior},
        dados_novos={"status": status_novo},
        perfil_usado=perfil_usado
    )


async def log_atualizar_config(
    service: AuditLogService,
    request: Request,
    usuario: Usuario,
    chave_config: str,
    valor_anterior: Any,
    valor_novo: Any,
    perfil_usado: Optional[str] = None
):
    """Helper para logar alteração de configuração"""
    return await service.criar_log_from_request(
        request=request,
        usuario=usuario,
        acao=AcaoAuditoria.ATUALIZAR_CONFIG,
        entidade=EntidadeAuditoria.CONFIG,
        descricao=f"Atualizou configuração '{chave_config}'",
        dados_anteriores={"chave": chave_config, "valor": valor_anterior},
        dados_novos={"chave": chave_config, "valor": valor_novo},
        perfil_usado=perfil_usado
    )
