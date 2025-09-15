# app/services/pendencia_service.py
from typing import List, Optional
from fastapi import HTTPException, status

# Repositórios
from app.repositories.pendencia_repo import PendenciaRepository
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.status_pendencia_repo import StatusPendenciaRepository

# Schemas
from app.schemas.pendencia_schema import Pendencia, PendenciaCreate

class PendenciaService:
    def __init__(self,
                 pendencia_repo: PendenciaRepository,
                 contrato_repo: ContratoRepository,
                 usuario_repo: UsuarioRepository,
                 status_pendencia_repo: StatusPendenciaRepository):
        self.pendencia_repo = pendencia_repo
        self.contrato_repo = contrato_repo
        self.usuario_repo = usuario_repo
        self.status_pendencia_repo = status_pendencia_repo

    async def _validate_foreign_keys(self, pendencia: PendenciaCreate, contrato_id: int):
        """Valida a existência de IDs antes de criar a pendência."""
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
        
        if not await self.usuario_repo.get_user_by_id(pendencia.criado_por_usuario_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário criador não encontrado")

        if not await self.status_pendencia_repo.get_by_id(pendencia.status_pendencia_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de pendência não encontrado")

    async def create_pendencia(self, contrato_id: int, pendencia_create: PendenciaCreate) -> Pendencia:
        """Cria uma nova pendência para um contrato."""
        await self._validate_foreign_keys(pendencia_create, contrato_id)
        
        # Lógica de notificação por e-mail pode ser adicionada aqui no futuro
        
        new_pendencia_data = await self.pendencia_repo.create_pendencia(contrato_id, pendencia_create)
        return Pendencia.model_validate(new_pendencia_data)

    async def get_pendencias_by_contrato_id(self, contrato_id: int) -> List[Pendencia]:
        """Lista todas as pendências de um contrato específico."""
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
            
        pendencias_data = await self.pendencia_repo.get_pendencias_by_contrato_id(contrato_id)
        return [Pendencia.model_validate(p) for p in pendencias_data]