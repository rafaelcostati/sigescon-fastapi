# app/api/routers/auth_router.py
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import get_connection
from app.repositories.usuario_repo import UsuarioRepository
from app.schemas.token_schema import Token
from app.core.security import verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: asyncpg.Connection = Depends(get_connection)
):
    user_repo = UsuarioRepository(conn)
    user = await user_repo.get_user_by_email(form_data.username) # O form usa 'username' para o email

    if not user or not verify_password(form_data.password, user['senha']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user['id'])})

    return {"access_token": access_token, "token_type": "bearer"}