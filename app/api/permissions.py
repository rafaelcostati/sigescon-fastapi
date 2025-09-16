# app/api/permissions.py 
from typing import List
from fastapi import HTTPException, status, Depends
import asyncpg

from app.api.dependencies import get_current_user, get_connection
from app.schemas.usuario_schema import Usuario
from app.repositories.perfil_repo import PerfilRepository
from app.repositories.contrato_repo import ContratoRepository

class PermissionChecker:
    """Classe para verificação de permissões específicas"""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.perfil_repo = PerfilRepository(conn)
        self.contrato_repo = ContratoRepository(conn)

    async def has_role(self, user: Usuario, roles: List[str]) -> bool:
        """Verifica se o usuário tem um dos papéis especificados"""
        perfil = await self.perfil_repo.get_perfil_by_id(user.perfil_id)
        return perfil and perfil.get("nome") in roles

    async def is_contract_stakeholder(self, user: Usuario, contrato_id: int) -> bool:
        """Verifica se o usuário é gestor ou fiscal do contrato"""
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if not contrato:
            return False
        
        return user.id in [contrato.get('gestor_id'), contrato.get('fiscal_id'), contrato.get('fiscal_substituto_id')]

    async def can_access_contract(self, user: Usuario, contrato_id: int) -> bool:
        """Verifica se o usuário pode acessar dados do contrato"""
        # Admin pode tudo
        if await self.has_role(user, ["Administrador"]):
            return True
        
        # Gestor/Fiscal podem acessar seus contratos
        return await self.is_contract_stakeholder(user, contrato_id)

# === DEPENDÊNCIAS DE PERMISSÃO ===

async def require_admin(
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:
    """Requer perfil de Administrador"""
    checker = PermissionChecker(conn)
    if not await checker.has_role(current_user, ["Administrador"]):
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
    if not await checker.has_role(current_user, ["Administrador", "Gestor"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores e gestores"
        )
    return current_user

