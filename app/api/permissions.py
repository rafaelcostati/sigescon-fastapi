# app/api/permissions.py 
from typing import List
from fastapi import HTTPException, status, Depends
import asyncpg

from app.api.dependencies import get_current_user, get_connection, get_current_user_with_context
from app.schemas.usuario_schema import Usuario
from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository
from app.repositories.contrato_repo import ContratoRepository

class PermissionChecker:
    """Classe para verificação de permissões com sistema de perfis múltiplos"""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.usuario_perfil_repo = UsuarioPerfilRepository(conn)
        self.contrato_repo = ContratoRepository(conn)

    async def has_profile(self, user: Usuario, profile_name: str) -> bool:
        """Verifica se o usuário tem um perfil específico"""
        return await self.usuario_perfil_repo.has_profile(user.id, profile_name)

    async def has_any_profile(self, user: Usuario, profile_names: List[str]) -> bool:
        """Verifica se o usuário tem pelo menos um dos perfis especificados"""
        return await self.usuario_perfil_repo.has_any_profile(user.id, profile_names)

    async def is_contract_stakeholder(self, user: Usuario, contrato_id: int) -> bool:
        """Verifica se o usuário é gestor ou fiscal do contrato"""
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if not contrato:
            return False
        
        return user.id in [contrato.get('gestor_id'), contrato.get('fiscal_id'), contrato.get('fiscal_substituto_id')]

    async def can_access_contract(self, user: Usuario, contrato_id: int, perfil_ativo: str = None) -> bool:
        """Verifica se o usuário pode acessar dados do contrato baseado no perfil ativo"""
        # Se não foi informado perfil ativo, verifica se é admin geral
        if not perfil_ativo:
            if await self.has_profile(user, "Administrador"):
                return True
            return await self.is_contract_stakeholder(user, contrato_id)

        # Com perfil ativo, verifica contexto específico
        if perfil_ativo == "Administrador":
            return True  # Admin sempre pode acessar

        # Para outros perfis, verifica se está relacionado ao contrato
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if not contrato:
            return False

        if perfil_ativo == "Gestor":
            return user.id == contrato.get('gestor_id')
        elif perfil_ativo == "Fiscal":
            return user.id in [contrato.get('fiscal_id'), contrato.get('fiscal_substituto_id')]

        return False

    async def can_be_fiscal(self, user_id: int) -> bool:
        """Verifica se o usuário pode exercer função de fiscal em contratos"""
        return await self.usuario_perfil_repo.validate_user_can_be_fiscal(user_id)

    async def can_be_manager(self, user_id: int) -> bool:
        """Verifica se o usuário pode exercer função de gestor em contratos"""
        return await self.usuario_perfil_repo.validate_user_can_be_manager(user_id)

async def require_admin(
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:
    """Requer perfil de Administrador"""
    checker = PermissionChecker(conn)
    if not await checker.has_profile(current_user, "Administrador"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return current_user

async def require_admin_or_manager(
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:
    """Requer perfil de Administrador ou Gestor"""
    checker = PermissionChecker(conn)
    if not await checker.has_any_profile(current_user, ["Administrador", "Gestor"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores e gestores"
        )
    return current_user

async def require_admin_or_fiscal(
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:
    """Requer perfil de Administrador ou Fiscal"""
    checker = PermissionChecker(conn)
    if not await checker.has_any_profile(current_user, ["Administrador", "Fiscal"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores e fiscais"
        )
    return current_user

async def require_any_profile(
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:
    """Permite qualquer usuário com pelo menos um perfil ativo"""
    checker = PermissionChecker(conn)
    profiles = await checker.usuario_perfil_repo.get_user_profiles(current_user.id)
    
    if not profiles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem perfis ativos no sistema"
        )
    return current_user

admin_required = require_admin

# Funções de permissão baseadas no contexto ativo
async def require_active_admin(
    user_context: tuple = Depends(get_current_user_with_context)
) -> tuple:
    """Requer que o perfil ativo seja Administrador"""
    current_user, context = user_context

    if context.perfil_ativo_nome != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta ação requer que você esteja no perfil de Administrador"
        )
    return user_context

async def require_active_admin_or_manager(
    user_context: tuple = Depends(get_current_user_with_context)
) -> tuple:
    """Requer que o perfil ativo seja Administrador ou Gestor"""
    current_user, context = user_context

    if context.perfil_ativo_nome not in ["Administrador", "Gestor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta ação requer perfil de Administrador ou Gestor ativo"
        )
    return user_context

async def require_active_admin_or_fiscal(
    user_context: tuple = Depends(get_current_user_with_context)
) -> tuple:
    """Requer que o perfil ativo seja Administrador ou Fiscal"""
    current_user, context = user_context

    if context.perfil_ativo_nome not in ["Administrador", "Fiscal"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta ação requer perfil de Administrador ou Fiscal ativo"
        )
    return user_context

# Alias para compatibilidade
active_admin_required = require_active_admin