# app/services/pendencia_service.py
from typing import List
from fastapi import HTTPException, status

# Repositórios
from app.repositories.pendencia_repo import PendenciaRepository
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.status_pendencia_repo import StatusPendenciaRepository

# Schemas
from app.schemas.pendencia_schema import Pendencia, PendenciaCreate

# --- INTEGRAÇÃO ---
from app.services.email_service import EmailService

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
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
        
        if not await self.usuario_repo.get_user_by_id(pendencia.criado_por_usuario_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário criador não encontrado")

        if not await self.status_pendencia_repo.get_by_id(pendencia.status_pendencia_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de pendência não encontrado")

    async def create_pendencia(self, contrato_id: int, pendencia_create: PendenciaCreate) -> Pendencia:
        await self._validate_foreign_keys(pendencia_create, contrato_id)
        
        new_pendencia_data = await self.pendencia_repo.create_pendencia(contrato_id, pendencia_create)
        
        # --- LÓGICA DE E-MAIL ADICIONADA ---
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if contrato and contrato.get('fiscal_id'):
            fiscal = await self.usuario_repo.get_user_by_id(contrato['fiscal_id'])
            if fiscal:
                subject = "Nova pendência de relatório registada para si"
                body = f"""
Olá, {fiscal['nome']},

Uma nova pendência de relatório foi registada para o contrato '{contrato['nr_contrato']}':

- Descrição: {new_pendencia_data['descricao']}
- Prazo para envio: {new_pendencia_data['data_prazo'].strftime('%d/%m/%Y')}

Por favor, aceda ao sistema para submeter o relatório.
                """
                await EmailService.send_email(fiscal['email'], subject, body)
        
        return Pendencia.model_validate(new_pendencia_data)

    async def get_pendencias_by_contrato_id(self, contrato_id: int) -> List[Pendencia]:
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
            
        pendencias_data = await self.pendencia_repo.get_pendencias_by_contrato_id(contrato_id)
        return [Pendencia.model_validate(p) for p in pendencias_data]