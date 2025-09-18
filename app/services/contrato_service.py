# app/services/contrato_service.py
import math
from typing import Optional, Dict
from fastapi import HTTPException, logger, status, UploadFile

# Repositórios
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.contratado_repo import ContratadoRepository as ContratadoRepo
from app.repositories.modalidade_repo import ModalidadeRepository
from app.repositories.status_repo import StatusRepository
from app.repositories.arquivo_repo import ArquivoRepository

# Services
from app.services.file_service import FileService
from app.services.email_service import EmailService

# Schemas
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
                 status_repo: StatusRepository,
                 arquivo_repo: ArquivoRepository,
                 file_service: FileService):
        self.contrato_repo = contrato_repo
        self.usuario_repo = usuario_repo
        self.contratado_repo = contratado_repo
        self.modalidade_repo = modalidade_repo
        self.status_repo = status_repo
        self.arquivo_repo = arquivo_repo
        self.file_service = file_service

    async def _validate_foreign_keys(self, contrato: ContratoCreate | ContratoUpdate):
        """Valida se todas as chaves estrangeiras existem"""
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

    async def _send_contract_assignment_email(self, contrato_data: Dict, fiscal_id: int, gestor_id: int, is_update: bool = False, old_fiscal_id: Optional[int] = None):
        """Envia emails de notificação para fiscal e gestor quando um contrato é criado ou atualizado"""
        from app.services.email_templates import EmailTemplates
        
        # Email para o fiscal (novo ou atual)
        if fiscal_id:
            fiscal = await self.usuario_repo.get_user_by_id(fiscal_id)
            if fiscal:
                subject, body = EmailTemplates.contract_assignment_fiscal(
                    fiscal_nome=fiscal['nome'],
                    contrato_data=contrato_data,
                    is_new=not is_update
                )
                await EmailService.send_email(fiscal['email'], subject, body)

        # Email para o gestor
        if gestor_id:
            gestor = await self.usuario_repo.get_user_by_id(gestor_id)
            if gestor:
                # Busca dados do fiscal para incluir no email do gestor
                fiscal_data = None
                if fiscal_id:
                    fiscal = await self.usuario_repo.get_user_by_id(fiscal_id)
                    if fiscal:
                        fiscal_data = {'nome': fiscal['nome'], 'email': fiscal['email']}
                
                subject, body = EmailTemplates.contract_assignment_manager(
                    gestor_nome=gestor['nome'],
                    contrato_data=contrato_data,
                    fiscal_data=fiscal_data,
                    is_new=not is_update
                )
                await EmailService.send_email(gestor['email'], subject, body)

        # Se houve mudança de fiscal, notifica o fiscal anterior
        if is_update and old_fiscal_id and old_fiscal_id != fiscal_id:
            old_fiscal = await self.usuario_repo.get_user_by_id(old_fiscal_id)
            if old_fiscal:
                # Busca nome do novo fiscal para incluir na notificação
                novo_fiscal_nome = None
                if fiscal_id:
                    novo_fiscal = await self.usuario_repo.get_user_by_id(fiscal_id)
                    if novo_fiscal:
                        novo_fiscal_nome = novo_fiscal['nome']
                
                subject, body = EmailTemplates.contract_transfer_notification(
                    fiscal_nome=old_fiscal['nome'],
                    contrato_data=contrato_data,
                    novo_fiscal_nome=novo_fiscal_nome
                )
                await EmailService.send_email(old_fiscal['email'], subject, body)

    async def create_contrato(self, contrato_create: ContratoCreate, file: Optional[UploadFile] = None) -> Contrato:
        """Cria um novo contrato e, opcionalmente, anexa um arquivo"""
        await self._validate_foreign_keys(contrato_create)
        
        # Cria o contrato primeiro para obter um ID
        new_contrato_data = await self.contrato_repo.create_contrato(contrato_create)
        contrato_id = new_contrato_data['id']

        # Se um arquivo foi enviado, guarda-o e associa-o ao contrato
        if file:
            nome_original, path, tamanho = await self.file_service.save_upload_file(contrato_id, file)
            
            arquivo_data = await self.arquivo_repo.create_arquivo(
                nome_arquivo=nome_original,
                path_armazenamento=path,
                tipo_arquivo=file.content_type,
                tamanho_bytes=tamanho,
                contrato_id=contrato_id
            )
            # Vincula o ID do arquivo ao campo 'documento' do contrato
            await self.arquivo_repo.link_arquivo_to_contrato(arquivo_data['id'], contrato_id)
        
        # Retorna o contrato completo, agora com a informação do arquivo, se houver
        contrato_final = await self.contrato_repo.find_contrato_by_id(contrato_id)
        contrato_response = Contrato.model_validate(contrato_final)

        # Enviar emails de notificação 
        try:
            await self._send_contract_assignment_email(
                contrato_data=contrato_final,
                fiscal_id=contrato_create.fiscal_id,
                gestor_id=contrato_create.gestor_id,
                is_update=False
            )
        except Exception as e:
            # Log do erro, mas não falha a criação do contrato
            print(f"Erro ao enviar emails de notificação para contrato {contrato_id}: {e}")

        return contrato_response

    async def get_contrato_by_id(self, contrato_id: int) -> Optional[Contrato]:
        contrato_data = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if contrato_data:
            return Contrato.model_validate(contrato_data)
        return None

    async def get_all_contratos(self, page: int, per_page: int, filters: Optional[Dict] = None) -> ContratoPaginated:
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

    async def update_contrato(
        self, 
        contrato_id: int, 
        contrato_update: ContratoUpdate, 
        documento_contrato: Optional[UploadFile] = None
    ) -> Optional[Contrato]:
        """
        Atualiza um contrato existente, incluindo upload de arquivo opcional.
        
        Args:
            contrato_id: ID do contrato a atualizar
            contrato_update: Dados para atualização
            documento_contrato: Arquivo opcional para upload
            
        Returns:
            Contrato atualizado ou None se não encontrado
        """
        
        try:
            # Verifica se o contrato existe
            existing_contrato = await self.contrato_repo.get_by_id(contrato_id)
            if not existing_contrato:
                return None
            
            # Processa arquivo se fornecido
            update_data = contrato_update.model_dump(exclude_none=True)
            
            if documento_contrato and documento_contrato.filename:
                # Salva o novo arquivo
                original_filename, file_path, file_size = await self.file_service.save_upload_file(
                    contrato_id=contrato_id,
                    file=documento_contrato
                )
                
                # Remove arquivo antigo se existir
                if existing_contrato.get('documento_caminho'):
                    try:
                        import os
                        if os.path.exists(existing_contrato['documento_caminho']):
                            os.remove(existing_contrato['documento_caminho'])
                    except Exception as e:
                        # Log do erro mas não interrompe o processo
                        logger.warning(f"Erro ao remover arquivo antigo: {e}")
                
                # Atualiza dados do arquivo no contrato
                update_data.update({
                    'documento_nome_arquivo': original_filename,
                    'documento_caminho': file_path,
                    'documento_tamanho': file_size
                })
            
            # Executa a atualização no banco
            updated_contrato = await self.contrato_repo.update(contrato_id, update_data)
            
            return updated_contrato
            
        except Exception as e:
            logger.error(f"Erro ao atualizar contrato {contrato_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno ao atualizar contrato: {str(e)}"
            )

    async def delete_contrato(self, contrato_id: int) -> bool:
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
        return await self.contrato_repo.delete_contrato(contrato_id)