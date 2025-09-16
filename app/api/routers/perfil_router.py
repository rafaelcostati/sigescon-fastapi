# app/api/routers/perfil_router.py
import asyncpg
from fastapi import APIRouter, Depends, status
from typing import List

from app.core.database import get_connection
from app.schemas.perfil_schema import Perfil, PerfilCreate
from app.services.perfil_service import PerfilService
from app.repositories.perfil_repo import PerfilRepository
from app.api.dependencies import get_current_user, get_current_admin_user
from app.schemas.usuario_schema import Usuario
from app.api.permissions import admin_required

router = APIRouter(
    prefix="/perfis",
    tags=["Perfis"]
)

def get_perfil_service(conn: asyncpg.Connection = Depends(get_connection)):
    repo = PerfilRepository(conn)
    return PerfilService(repo)

@router.post("/", response_model=Perfil, status_code=status.HTTP_201_CREATED)
async def create_perfil(
    perfil: PerfilCreate,
    service: PerfilService = Depends(get_perfil_service),
    admin_user: Usuario = Depends(admin_required)
):
    return await service.create(perfil)

@router.get("/", response_model=List[Perfil])
async def get_all_perfis(
    service: PerfilService = Depends(get_perfil_service),
    current_user: Usuario = Depends(get_current_user)
):
    return await service.get_all()