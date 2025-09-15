# app/api/dependencies.py
import asyncpg
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_connection
from app.repositories.usuario_repo import UsuarioRepository
from app.schemas.token_schema import TokenData
from app.schemas.usuario_schema import Usuario
from app.repositories.perfil_repo import PerfilRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


  
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    conn: asyncpg.Connection = Depends(get_connection)
) -> Usuario:
    """
    Decodifica o token JWT para obter o ID do usuário,
    busca o usuário no banco e retorna os dados dele.
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
    Verifica se o usuário logado é um Administrador.
    Reutiliza a dependência get_current_user.
    """
    perfil_repo = PerfilRepository(conn)
    perfil = await perfil_repo.get_perfil_by_id(current_user.perfil_id)

    if not perfil or perfil.get("nome") != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user