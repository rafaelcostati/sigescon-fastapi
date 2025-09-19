# app/api/routers/usuario_perfil_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List

from app.core.database import get_connection
from app.schemas.usuario_schema import Usuario
from app.api.dependencies import get_current_user
from app.api.permissions import admin_required

# Repositórios e Services
from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.perfil_repo import PerfilRepository
from app.services.usuario_perfil_service import UsuarioPerfilService

# Schemas
from app.schemas.usuario_perfil_schema import (
    UsuarioPerfil, UsuarioComPerfis, PerfilWithUsers,
    HistoricoPerfilConcessao, ValidacaoPerfil,
    UsuarioPerfilGrantRequest, UsuarioPerfilRevokeRequest
)

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Perfis de Usuários"]
)

# --- Injeção de Dependências ---
def get_usuario_perfil_service(conn: asyncpg.Connection = Depends(get_connection)) -> UsuarioPerfilService:
    return UsuarioPerfilService(
        usuario_perfil_repo=UsuarioPerfilRepository(conn),
        usuario_repo=UsuarioRepository(conn),
        perfil_repo=PerfilRepository(conn)
    )

# --- Endpoints ---

@router.get("/{usuario_id}/perfis", response_model=List[UsuarioPerfil])
async def get_user_profiles(
    usuario_id: int,
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos os perfis ativos de um usuário específico"""
    # Usuários podem ver seus próprios perfis, admins podem ver de qualquer usuário
    if current_user.id != usuario_id:
        # Verifica se é admin usando o service que já tem a conexão
        if not await service.has_profile(current_user.id, "Administrador"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode visualizar seus próprios perfis"
            )
    
    return await service.get_user_profiles(usuario_id)

@router.get("/{usuario_id}/perfis/completo", response_model=UsuarioComPerfis)
async def get_user_complete_info(
    usuario_id: int,
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Busca informações completas do usuário incluindo todos os perfis"""
    # Mesma validação de permissão
    if current_user.id != usuario_id:
        # Verifica se é admin usando o service que já tem a conexão
        if not await service.has_profile(current_user.id, "Administrador"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode visualizar suas próprias informações"
            )
    
    return await service.get_user_complete_info(usuario_id)

@router.post("/{usuario_id}/perfis/conceder", response_model=List[UsuarioPerfil])
async def grant_profiles_to_user(
    usuario_id: int,
    request: UsuarioPerfilGrantRequest,
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    admin_user: Usuario = Depends(admin_required)
):
    """Concede múltiplos perfis a um usuário (Requer permissão de administrador)"""
    return await service.grant_profiles_to_user(usuario_id, request, admin_user.id)

@router.post("/{usuario_id}/perfis/revogar", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_profiles_from_user(
    usuario_id: int,
    request: UsuarioPerfilRevokeRequest,
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    admin_user: Usuario = Depends(admin_required)
):
    """Revoga múltiplos perfis de um usuário (Requer permissão de administrador)"""
    success = await service.revoke_profiles_from_user(usuario_id, request)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum perfil foi revogado"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{usuario_id}/perfis/historico", response_model=List[HistoricoPerfilConcessao])
async def get_profile_history(
    usuario_id: int,
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    admin_user: Usuario = Depends(admin_required)
):
    """Busca histórico completo de concessão/remoção de perfis de um usuário"""
    return await service.get_profile_history(usuario_id)

@router.get("/{usuario_id}/perfis/validacao", response_model=ValidacaoPerfil)
async def validate_user_permissions(
    usuario_id: int,
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Valida as permissões e capacidades de um usuário"""
    # Permite que usuários vejam suas próprias validações
    if current_user.id != usuario_id:
        # Verifica se é admin usando o service que já tem a conexão
        if not await service.has_profile(current_user.id, "Administrador"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode validar suas próprias permissões"
            )
    
    return await service.validate_user_permissions(usuario_id)

# --- Endpoints para Listagens Especiais ---

@router.get("/fiscais-disponiveis", response_model=List[UsuarioComPerfis])
async def get_available_fiscals(
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos os usuários que podem exercer função de fiscal"""
    return await service.get_available_fiscals()

@router.get("/gestores-disponiveis", response_model=List[UsuarioComPerfis])
async def get_available_managers(
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos os usuários que podem exercer função de gestor"""
    return await service.get_available_managers()

# --- Endpoints para Perfis Específicos ---

@router.get("/por-perfil/{perfil_name}", response_model=PerfilWithUsers)
async def get_users_by_profile(
    perfil_name: str,
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    admin_user: Usuario = Depends(admin_required)
):
    """Lista todos os usuários que possuem um perfil específico"""
    return await service.get_users_by_profile(perfil_name)

# --- Endpoints para Migração e Operações em Lote ---

@router.post("/{usuario_id}/perfis/migrar", response_model=UsuarioComPerfis)
async def migrate_user_to_multiple_profiles(
    usuario_id: int,
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    admin_user: Usuario = Depends(admin_required)
):
    """Migra um usuário do sistema de perfil único para perfis múltiplos"""
    return await service.migrate_single_profile_user(usuario_id, admin_user.id)

@router.post("/perfis/conceder-lote")
async def bulk_grant_profile(
    usuario_ids: List[int],
    perfil_id: int,
    observacoes: str = None,
    service: UsuarioPerfilService = Depends(get_usuario_perfil_service),
    admin_user: Usuario = Depends(admin_required)
):
    """Concede um perfil a múltiplos usuários de uma vez"""
    return await service.bulk_grant_profile(usuario_ids, perfil_id, admin_user.id, observacoes)