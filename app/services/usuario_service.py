# app/services/usuario_service.py
import math
from typing import Optional, List, Dict
from fastapi import HTTPException, status
from app.repositories.usuario_repo import UsuarioRepository
from app.schemas.usuario_schema import (
    Usuario, UsuarioCreate, UsuarioUpdate, 
    UsuarioChangePassword, UsuarioResetPassword,
    UsuarioPaginated, UsuarioList
)
from app.core.security import get_password_hash, verify_password

class UsuarioService:
    def __init__(self, usuario_repo: UsuarioRepository):
        self.usuario_repo = usuario_repo

    async def get_all_paginated(
        self, page: int, per_page: int, filters: Optional[Dict] = None
    ) -> UsuarioPaginated:
        """Lista todos os usuários com paginação e filtros."""
        offset = (page - 1) * per_page
        users_data, total_items = await self.usuario_repo.get_all_users_paginated(
            filters=filters, limit=per_page, offset=offset
        )
        
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
        
        return UsuarioPaginated(
            data=[UsuarioList.model_validate(u) for u in users_data],
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            per_page=per_page
        )

    async def get_by_id(self, user_id: int) -> Optional[Usuario]:
        """Busca um usuário pelo ID"""
        user_data = await self.usuario_repo.get_user_by_id(user_id)
        if user_data:
            return Usuario.model_validate(user_data)
        return None

    async def create_user(self, user_create: UsuarioCreate) -> Usuario:
        """Cria um novo usuário"""
        # Verifica se o email já existe
        if await self.usuario_repo.check_email_exists(user_create.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Um usuário com este email já existe"
            )

        # Hash da senha
        hashed_password = get_password_hash(user_create.senha)
        
        # Cria o usuário
        new_user_data = await self.usuario_repo.create_user(user_create, hashed_password)
        return Usuario.model_validate(new_user_data)

    async def update_user(self, user_id: int, user_update: UsuarioUpdate) -> Optional[Usuario]:
        """Atualiza dados de um usuário"""
        # Verifica se o usuário existe
        existing_user = await self.usuario_repo.get_user_by_id(user_id)
        if not existing_user:
            return None

        # Se está atualizando o email, verifica se já existe
        if user_update.email and user_update.email != existing_user['email']:
            if await self.usuario_repo.check_email_exists(user_update.email, exclude_id=user_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Este email já está em uso por outro usuário"
                )

        # Se está atualizando a senha, faz o hash
        if user_update.senha:
            hashed_password = get_password_hash(user_update.senha)
            await self.usuario_repo.update_user_password(user_id, hashed_password)
            # Remove a senha do update para não tentar atualizar no campo errado
            user_update.senha = None

        # Atualiza os outros campos
        updated_data = await self.usuario_repo.update_user(user_id, user_update)
        if updated_data:
            return Usuario.model_validate(updated_data)
        return None

    async def delete_user(self, user_id: int) -> bool:
        """Soft delete de um usuário"""
        # Verifica se o usuário existe
        if not await self.usuario_repo.get_user_by_id(user_id):
            return False
        
        return await self.usuario_repo.delete_user(user_id)

    async def change_password(self, user_id: int, password_data: UsuarioChangePassword) -> bool:
        """Permite que o usuário altere sua própria senha"""
        # Busca o usuário com a senha atual
        user_with_password = await self.usuario_repo.get_user_with_password(user_id)
        if not user_with_password:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Verifica a senha antiga
        if not verify_password(password_data.senha_antiga, user_with_password['senha']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Senha antiga incorreta"
            )

        # Atualiza para a nova senha
        new_hash = get_password_hash(password_data.nova_senha)
        return await self.usuario_repo.update_user_password(user_id, new_hash)

    async def reset_password(self, user_id: int, reset_data: UsuarioResetPassword) -> bool:
        """Admin reseta a senha de um usuário"""
        # Verifica se o usuário existe
        if not await self.usuario_repo.get_user_by_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Reseta a senha
        new_hash = get_password_hash(reset_data.nova_senha)
        return await self.usuario_repo.update_user_password(user_id, new_hash)

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """Busca um usuário pelo email"""
        user_data = await self.usuario_repo.get_user_by_email(email)
        if user_data:
            # Remove a senha antes de retornar
            user_data.pop('senha', None)
            return Usuario.model_validate(user_data)
        return None