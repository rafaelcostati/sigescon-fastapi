# app/api/doc_dependencies.py
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import asyncpg

from app.core.database import get_connection
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.perfil_repo import PerfilRepository
from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository
from app.core.security import verify_password
from app.core.config import settings

security = HTTPBasic()

async def get_admin_for_docs(
    credentials: HTTPBasicCredentials = Security(security),
    conn: asyncpg.Connection = Depends(get_connection)
):
    """
    Dependência para verificar credenciais de administrador para acessar a documentação.
    Utiliza autenticação HTTPBasic.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou acesso não autorizado",
        headers={"WWW-Authenticate": "Basic"},
    )
    
    user_repo = UsuarioRepository(conn)

    correct_username = settings.ADMIN_EMAIL
    user = await user_repo.get_user_by_email(credentials.username)

    # Validações seguras
    if not (
        user
        and secrets.compare_digest(credentials.username, correct_username or "")
        and verify_password(credentials.password, user['senha_hash'])
    ):
        raise credentials_exception

    # Verificar se o usuário tem perfil de administrador
    usuario_perfil_repo = UsuarioPerfilRepository(conn)
    is_admin = await usuario_perfil_repo.has_profile(user['id'], "Administrador")

    if not is_admin:
        raise credentials_exception
    
    return True