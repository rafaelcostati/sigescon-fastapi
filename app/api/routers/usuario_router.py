# app/api/routers/usuario_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.usuario_schema import Usuario, UsuarioCreate
from app.api.dependencies import get_current_user, get_current_admin_user
from app.services.usuario_service import UsuarioService
from app.repositories.usuario_repo import UsuarioRepository
from app.core.database import get_connection
import asyncpg

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

# Dependência para o serviço de usuário
def get_usuario_service(conn: asyncpg.Connection = Depends(get_connection)):
    repo = UsuarioRepository(conn)
    return UsuarioService(repo)

@router.get("/me", response_model=Usuario)
async def read_users_me(current_user: Usuario = Depends(get_current_user)):
    """Retorna os dados do usuário logado."""
    return current_user

@router.post("/", response_model=Usuario, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
    admin_user: Usuario = Depends(get_current_admin_user) 
):
    """Cria um novo usuário (apenas para administradores)."""
    new_user = await service.create_user(user)
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um usuário com este email já existe."
        )
    return new_user

@router.get("/{user_id}", response_model=Usuario)
async def get_user_by_id(
    user_id: int,
    service: UsuarioService = Depends(get_usuario_service),
    current_user: Usuario = Depends(get_current_user) 
):
    """Busca um usuário pelo ID."""
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return user