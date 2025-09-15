# app/services/usuario_service.py
from typing import Optional
from app.repositories.usuario_repo import UsuarioRepository
from app.schemas.usuario_schema import Usuario, UsuarioCreate
from app.core.security import get_password_hash

class UsuarioService:
    def __init__(self, usuario_repo: UsuarioRepository):
        self.usuario_repo = usuario_repo

    async def get_by_id(self, user_id: int) -> Optional[Usuario]:
        user_data = await self.usuario_repo.get_user_by_id(user_id)
        if user_data:
            return Usuario.model_validate(user_data)
        return None

    async def create_user(self, user_create: UsuarioCreate) -> Usuario:
        # Lógica de negócio: Verificar se o email já existe
        user_in_db = await self.usuario_repo.get_user_by_email(user_create.email)
        if user_in_db:
            # No mundo real, lançaríamos uma exceção customizada aqui
            return None 

        hashed_password = get_password_hash(user_create.senha)
        new_user_data = await self.usuario_repo.create_user(user_create, hashed_password)
        return Usuario.model_validate(new_user_data)