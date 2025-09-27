# app/api/routers/usuario_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import List, Optional

from app.schemas.usuario_schema import (
    Usuario, UsuarioCreate, UsuarioUpdate,
    UsuarioChangePassword, UsuarioResetPassword, UsuarioPaginated 
)
from app.schemas.usuario_perfil_schema import UsuarioPerfilGrantRequest
from app.api.dependencies import get_current_user
from app.services.usuario_service import UsuarioService
from app.repositories.usuario_repo import UsuarioRepository
from app.core.database import get_connection
import asyncpg
from app.api.permissions import admin_required, require_admin_or_manager, require_any_profile


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

# Dependência para o serviço de usuário
def get_usuario_service(conn: asyncpg.Connection = Depends(get_connection)):
    repo = UsuarioRepository(conn)
    return UsuarioService(repo)

@router.get("/me", response_model=Usuario, summary="Obter dados do usuário logado")
async def read_users_me(current_user: Usuario = Depends(get_current_user)):
    """
    Retorna os dados do usuário atualmente autenticado.
    
    Requer autenticação válida.
    """
    return current_user

@router.get("/test")
async def test_usuarios():
    """Rota de teste para verificar se o router está funcionando"""
    print("🔍 TESTE - Rota /usuarios/test chamada com sucesso!")
    return {"message": "Router de usuários funcionando!", "timestamp": "2025-09-27"}

@router.get("", response_model=UsuarioPaginated, summary="Listar todos os usuários")
async def list_users(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(10, ge=1, le=100, description="Itens por página"),
    nome: Optional[str] = Query(None, description="Filtrar por nome (busca parcial)"),
    perfil: Optional[str] = Query(None, description="Filtrar por perfil (Administrador, Gestor, Fiscal)"),
    service: UsuarioService = Depends(get_usuario_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos os usuários ativos do sistema com paginação.

    Permite filtrar por nome (busca parcial) e por perfil.

    **Requer usuário com perfil ativo (Administrador, Gestor ou Fiscal).**
    """
    print(f"🔍 USUARIOS - GET / chamado com page={page}, per_page={per_page}")
    print(f"🔍 USUARIOS - Filtros: nome={nome}, perfil={perfil}")
    print(f"🔍 USUARIOS - Usuário: {current_user.nome} (ID: {current_user.id})")
    
    filters = {}
    if nome:
        filters['nome'] = nome
    if perfil:
        filters['perfil'] = perfil
    
    result = await service.get_all_paginated(page=page, per_page=per_page, filters=filters)
    print(f"🔍 USUARIOS - Retornando {len(result.data)} itens de {result.total_items} total")
    return result

# Rota POST com barra final
@router.post("/", response_model=Usuario, status_code=status.HTTP_201_CREATED, summary="Criar novo usuário")
async def create_user_with_slash(
    user: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
    admin_user: Usuario = Depends(admin_required)
):
    """Cria um novo usuário no sistema SEM PERFIL (rota com barra final)"""
    return await service.create_user(user)

# Rota POST sem barra final
@router.post("", response_model=Usuario, status_code=status.HTTP_201_CREATED, summary="Criar novo usuário")
async def create_user(
    user: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Cria um novo usuário no sistema SEM PERFIL.
    
    **Requer permissão de administrador.**
    
    **IMPORTANTE:** O usuário é criado sem perfil. Para conceder perfis, use:
    `POST /api/v1/usuarios/{user_id}/perfis/conceder`
    
    Validações:
    - Email deve ser único
    - CPF deve ter 11 dígitos
    - Senha deve ter no mínimo 6 caracteres
    - perfil_id é ignorado (sempre NULL)
    """
    return await service.create_user(user)

# Rota sem barra final (para evitar redirects do frontend)
@router.post("", response_model=Usuario, status_code=status.HTTP_201_CREATED, summary="Criar novo usuário")
async def create_user_without_slash(
    user: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Cria um novo usuário no sistema SEM PERFIL.

    **Requer permissão de administrador.**

    **IMPORTANTE:** O usuário é criado sem perfil. Para conceder perfis, use:
    `POST /api/v1/usuarios/{user_id}/perfis/conceder`

    Validações:
    - Email deve ser único
    - CPF deve ter 11 dígitos
    - Senha deve ter no mínimo 6 caracteres
    - perfil_id é ignorado (sempre NULL)
    """
    return await service.create_user(user)

@router.post("/com-perfis", response_model=Usuario, status_code=status.HTTP_201_CREATED, summary="Criar usuário e conceder perfis")
async def create_user_with_profiles(
    user: UsuarioCreate,
    perfil_ids: List[int],
    service: UsuarioService = Depends(get_usuario_service),
    admin_user: Usuario = Depends(admin_required),
    conn: asyncpg.Connection = Depends(get_connection)
):
    """
    Cria um novo usuário e concede perfis em uma única operação.
    
    **Requer permissão de administrador.**
    
    Este endpoint é uma conveniência que combina:
    1. Criação do usuário (sem perfil)
    2. Concessão dos perfis especificados
    
    Parâmetros:
    - user: Dados do usuário (perfil_id é ignorado)
    - perfil_ids: Lista de IDs dos perfis a serem concedidos
    """
    # 1. Criar o usuário
    new_user = await service.create_user(user)
    
    # 2. Conceder os perfis
    if perfil_ids:
        from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository
        from app.services.usuario_perfil_service import UsuarioPerfilService
        from app.repositories.perfil_repo import PerfilRepository
        
        usuario_perfil_service = UsuarioPerfilService(
            usuario_perfil_repo=UsuarioPerfilRepository(conn),
            usuario_repo=UsuarioRepository(conn),
            perfil_repo=PerfilRepository(conn)
        )
        
        grant_request = UsuarioPerfilGrantRequest(perfil_ids=perfil_ids)
        await usuario_perfil_service.grant_profiles_to_user(
            new_user.id, grant_request, admin_user.id
        )
    
    return new_user

@router.get("/{user_id}", response_model=Usuario, summary="Buscar usuário por ID")
async def get_user_by_id(
    user_id: int,
    service: UsuarioService = Depends(get_usuario_service),
    current_user: Usuario = Depends(require_any_profile)
):
    """
    Busca um usuário específico pelo ID.

    **Requer usuário com perfil ativo (Administrador, Gestor ou Fiscal).**
    """
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return user

@router.patch("/{user_id}", response_model=Usuario, summary="Atualizar usuário")
async def update_user(
    user_id: int,
    user_update: UsuarioUpdate,
    service: UsuarioService = Depends(get_usuario_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Atualiza os dados de um usuário existente.
    
    Todos os campos são opcionais - apenas os fornecidos serão atualizados.
    
    **Requer permissão de administrador.**
    """
    updated_user = await service.update_user(user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deletar usuário")
async def delete_user(
    user_id: int,
    service: UsuarioService = Depends(get_usuario_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Realiza soft delete de um usuário (marca como inativo).
    
    **Requer permissão de administrador.**
    """
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{user_id}/alterar-senha", summary="Alterar própria senha")
async def change_password(
    user_id: int,
    password_data: UsuarioChangePassword,
    service: UsuarioService = Depends(get_usuario_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Permite que um usuário altere sua própria senha.
    
    O usuário deve fornecer a senha antiga correta.
    
    **Nota:** Usuários só podem alterar sua própria senha.
    """
    # Verifica se o usuário está tentando alterar sua própria senha
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode alterar sua própria senha"
        )
    
    success = await service.change_password(user_id, password_data)
    if success:
        return {"message": "Senha alterada com sucesso"}
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Erro ao alterar senha"
    )

@router.patch("/{user_id}/resetar-senha", summary="Resetar senha de usuário")
async def reset_password(
    user_id: int,
    reset_data: UsuarioResetPassword,
    service: UsuarioService = Depends(get_usuario_service),
    admin_user: Usuario = Depends(admin_required)
):
    """
    Permite que um administrador resete a senha de qualquer usuário.
    
    **Requer permissão de administrador.**
    """
    success = await service.reset_password(user_id, reset_data)
    if success:
        return {"message": "Senha resetada com sucesso pelo administrador"}
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Erro ao resetar senha"
    )