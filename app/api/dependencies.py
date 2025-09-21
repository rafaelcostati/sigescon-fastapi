# app/api/dependencies.py 
import asyncpg
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional

from app.core.config import settings
from app.core.database import get_connection
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository
from app.repositories.session_context_repo import SessionContextRepository
from app.services.session_context_service import SessionContextService
from app.schemas.token_schema import TokenData
from app.schemas.usuario_schema import Usuario
from app.schemas.session_context_schema import ContextoSessao

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=int(user_id))
    except (JWTError, ValueError):
        raise credentials_exception

    user_repo = UsuarioRepository(conn)
    user_db = await user_repo.get_user_by_id(user_id=token_data.user_id)
    if user_db is None:
        raise credentials_exception

    return Usuario.model_validate(user_db)

async def get_current_admin_user(
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:
    """
    Verifica se o usuário tem perfil de Administrador no sistema de perfis múltiplos
    """
    usuario_perfil_repo = UsuarioPerfilRepository(conn)
    
    is_admin = await usuario_perfil_repo.has_profile(current_user.id, "Administrador")
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user

async def get_current_user_with_profiles(
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
) -> tuple[Usuario, list]:
    """
    Retorna o usuário atual e seus perfis ativos
    """
    usuario_perfil_repo = UsuarioPerfilRepository(conn)
    perfis = await usuario_perfil_repo.get_user_profiles(current_user.id)
    return current_user, perfis

async def get_current_fiscal_user(
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:
    """
    Verifica se o usuário pode exercer função de fiscal (Admin ou Fiscal)
    """
    usuario_perfil_repo = UsuarioPerfilRepository(conn)
    
    can_be_fiscal = await usuario_perfil_repo.has_any_profile(
        current_user.id, ["Administrador", "Fiscal"]
    )
    
    if not can_be_fiscal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a fiscais e administradores",
        )
    return current_user

async def get_current_manager_user(
    current_user: Usuario = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:
    """
    Verifica se o usuário pode exercer função de gestor (Admin ou Gestor)
    """
    usuario_perfil_repo = UsuarioPerfilRepository(conn)
    
    can_be_manager = await usuario_perfil_repo.has_any_profile(
        current_user.id, ["Administrador", "Gestor"]
    )
    
    if not can_be_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a gestores e administradores",
        )
    return current_user

async def get_token_payload(
    token: str = Depends(oauth2_scheme)
) -> dict:
    """
    Extrai e valida o payload do token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise credentials_exception

async def get_current_context(
    payload: dict = Depends(get_token_payload),
    conn: asyncpg.Connection = Depends(get_connection)
) -> ContextoSessao:
    """
    Retorna o contexto de sessão atual usando session_id do token
    """
    from app.repositories.contrato_repo import ContratoRepository

    session_service = SessionContextService(
        session_repo=SessionContextRepository(conn),
        usuario_repo=UsuarioRepository(conn),
        usuario_perfil_repo=UsuarioPerfilRepository(conn),
        contrato_repo=ContratoRepository(conn)
    )

    # Extrai session_id do token se disponível
    session_id = payload.get("session_id")
    user_id = payload.get("sub")

    if session_id:
        # Usa session_id para buscar contexto específico
        context = await session_service.get_session_context(session_id)
    else:
        # Fallback para busca por user_id (compatibilidade com tokens antigos)
        context = await session_service.get_session_context_by_user(int(user_id))

    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contexto de sessão não encontrado"
        )

    return context

async def get_current_user_with_context(
    current_user: Usuario = Depends(get_current_user),
    context: ContextoSessao = Depends(get_current_context)
) -> tuple[Usuario, ContextoSessao]:
    """
    Retorna o usuário atual e seu contexto de sessão
    """
    return current_user, context