# app/services/contratado_service.py
import math
from typing import List, Optional, Dict
from app.repositories.contratado_repo import ContratadoRepository
from app.schemas.contratado_schema import Contratado, ContratadoCreate, ContratadoUpdate, ContratadoPaginated

class ContratadoService:
    def __init__(self, contratado_repo: ContratadoRepository):
        self.contratado_repo = contratado_repo

    async def get_all(self) -> List[Contratado]:
        contratados_data = await self.contratado_repo.get_all_contratados()
        return [Contratado.model_validate(c) for c in contratados_data]

    async def get_all_paginated(
        self, 
        page: int = 1, 
        per_page: int = 10, 
        filters: Optional[Dict] = None
    ) -> ContratadoPaginated:
        # Calcula offset
        offset = (page - 1) * per_page
        
        # Busca dados paginados
        contratados_data, total_items = await self.contratado_repo.get_all_contratados_paginated(
            limit=per_page,
            offset=offset,
            filters=filters or {}
        )
        
        # Calcula total de páginas
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
        
        # Converte para schema
        contratados = [Contratado.model_validate(c) for c in contratados_data]
        
        return ContratadoPaginated(
            data=contratados,
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            per_page=per_page
        )

    async def get_by_id(self, contratado_id: int) -> Optional[Contratado]:
        contratado_data = await self.contratado_repo.get_contratado_by_id(contratado_id)
        if contratado_data:
            return Contratado.model_validate(contratado_data)
        return None

    async def create(self, contratado_create: ContratadoCreate) -> Contratado:
        new_contratado_data = await self.contratado_repo.create_contratado(contratado_create)
        return Contratado.model_validate(new_contratado_data)

    async def update(self, contratado_id: int, contratado_update: ContratadoUpdate) -> Optional[Contratado]:
        # Lógica de negócio: Primeiro, verifica se o contratado existe
        contratado_existente = await self.contratado_repo.get_contratado_by_id(contratado_id)
        if not contratado_existente:
            return None
        
        updated_data = await self.contratado_repo.update_contratado(contratado_id, contratado_update)
        return Contratado.model_validate(updated_data)

    async def delete(self, contratado_id: int) -> bool:
        # Lógica de negócio: Verifica se o contratado existe antes de tentar deletar
        contratado_existente = await self.contratado_repo.get_contratado_by_id(contratado_id)
        if not contratado_existente:
            return False # Retorna False se não encontrou para deletar
            
        return await self.contratado_repo.delete_contratado(contratado_id)