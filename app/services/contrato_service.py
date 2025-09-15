# app/services/contrato_service.py
import math
from typing import Optional, Dict
from fastapi import HTTPException, status

from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.contratado_repo import ContratadoRepository as ContratadoRepo
from app.repositories.modalidade_repo import ModalidadeRepository
from app.repositories.status_repo import StatusRepository

from app.schemas.contrato_schema import (
    Contrato, ContratoCreate, ContratoUpdate, 
    ContratoPaginated, ContratoList
)

class ContratoService:
    def __init__(self,
                 contrato_repo: ContratoRepository,
                 usuario_repo: UsuarioRepository,
                 contratado_repo: ContratadoRepo,
                 modalidade_repo: ModalidadeRepository,
                 status_repo: StatusRepository):
        self.contrato_repo = contrato_repo
        self.usuario_repo = usuario_repo
        self.contratado_repo = contratado_repo
        self.modalidade_repo = modalidade_repo
        self.status_repo = status_repo

    async def _validate_foreign_keys(self, contrato: ContratoCreate | ContratoUpdate):
        """Valida a existência de todos os IDs de chaves estrangeiras."""
        # O corpo do método permanece o mesmo
        if hasattr(contrato, 'contratado_id') and contrato.contratado_id and not await self.contratado_repo.get_contratado_by_id(contrato.contratado_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratado não encontrado")
        
        if hasattr(contrato, 'modalidade_id') and contrato.modalidade_id and not await self.modalidade_repo.get_modalidade_by_id(contrato.modalidade_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modalidade não encontrada")
            
        if hasattr(contrato, 'status_id') and contrato.status_id and not await self.status_repo.get_status_by_id(contrato.status_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status não encontrado")
            
        if hasattr(contrato, 'gestor_id') and contrato.gestor_id and not await self.usuario_repo.get_user_by_id(contrato.gestor_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gestor não encontrado")
            
        if hasattr(contrato, 'fiscal_id') and contrato.fiscal_id and not await self.usuario_repo.get_user_by_id(contrato.fiscal_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal não encontrado")
        
        if hasattr(contrato, 'fiscal_substituto_id') and contrato.fiscal_substituto_id and not await self.usuario_repo.get_user_by_id(contrato.fiscal_substituto_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal Substituto não encontrado")


    async def create_contrato(self, contrato_create: ContratoCreate) -> Contrato:
        """Cria um novo contrato após validar as chaves estrangeiras."""
        await self._validate_foreign_keys(contrato_create)
        new_contrato_data = await self.contrato_repo.create_contrato(contrato_create)
        return Contrato.model_validate(new_contrato_data)


    async def get_contrato_by_id(self, contrato_id: int) -> Optional[Contrato]:
        """Busca um contrato pelo ID."""
        contrato_data = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if contrato_data:
            return Contrato.model_validate(contrato_data)
        return None


    async def get_all_contratos(
        self,
        page: int,
        per_page: int,
        filters: Optional[Dict] = None
    ) -> ContratoPaginated:
        """Lista contratos de forma paginada com filtros."""
        offset = (page - 1) * per_page
        contratos_data, total_items = await self.contrato_repo.get_all_contratos(
            filters=filters,
            limit=per_page,
            offset=offset
        )
        
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1

        return ContratoPaginated(
            data=[ContratoList.model_validate(c) for c in contratos_data],
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            per_page=per_page
        )


    async def update_contrato(self, contrato_id: int, contrato_update: ContratoUpdate) -> Optional[Contrato]:
        """Atualiza um contrato existente."""
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            return None

        await self._validate_foreign_keys(contrato_update)
        
        updated_contrato_data = await self.contrato_repo.update_contrato(contrato_id, contrato_update)
        if updated_contrato_data:
            return Contrato.model_validate(updated_contrato_data)
        return None

    
    async def delete_contrato(self, contrato_id: int) -> bool:
        """Realiza o soft delete de um contrato."""
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
        
        return await self.contrato_repo.delete_contrato(contrato_id)