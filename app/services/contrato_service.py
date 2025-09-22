# app/services/contrato_service.py
import math
from typing import List, Optional, Dict
from fastapi import HTTPException, status, UploadFile
import logging

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

logger = logging.getLogger(__name__)
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
        if hasattr(contrato, 'contratado_id') and contrato.contratado_id:
            if not await self.contratado_repo.get_contratado_by_id(contrato.contratado_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratado não encontrado")
        
        if hasattr(contrato, 'modalidade_id') and contrato.modalidade_id:
            if not await self.modalidade_repo.get_modalidade_by_id(contrato.modalidade_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modalidade não encontrada")
        
        if hasattr(contrato, 'status_id') and contrato.status_id:
            if not await self.status_repo.get_status_by_id(contrato.status_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status não encontrado")
        
        if hasattr(contrato, 'gestor_id') and contrato.gestor_id:
            if not await self.usuario_repo.get_user_by_id(contrato.gestor_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gestor não encontrado")
        
        if hasattr(contrato, 'fiscal_id') and contrato.fiscal_id:
            if not await self.usuario_repo.get_user_by_id(contrato.fiscal_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal não encontrado")
        
        if hasattr(contrato, 'fiscal_substituto_id') and contrato.fiscal_substituto_id:
            if not await self.usuario_repo.get_user_by_id(contrato.fiscal_substituto_id):
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

    async def create_contrato(self, contrato_create: ContratoCreate, files: Optional[List[UploadFile]] = None) -> Contrato:
        """Cria um novo contrato e, opcionalmente, anexa múltiplos arquivos"""
        
        # Dados recebidos validados pelo Pydantic
        
        # Validação de chaves estrangeiras
        await self._validate_foreign_keys(contrato_create)
        
        # Validação de número duplicado
        if await self.contrato_repo.exists_nr_contrato(contrato_create.nr_contrato):
            next_available = await self.contrato_repo.get_next_available_nr_contrato()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Já existe um contrato ativo com o número '{contrato_create.nr_contrato}'. Sugestão: use o número '{next_available}'."
            )

        # Cria o contrato primeiro para obter um ID
        new_contrato_data = await self.contrato_repo.create_contrato(contrato_create)
        contrato_id = new_contrato_data['id']

        # Processamento de arquivos
        if files and any(file.filename for file in files if file):
            # Filtra apenas arquivos válidos
            valid_files = [file for file in files if file and file.filename and file.filename.strip()]

            if valid_files:
                saved_files = await self.file_service.save_multiple_upload_files(contrato_id, valid_files)

                # Salva cada arquivo no banco de dados
                for file_info in saved_files:
                    arquivo_data = await self.arquivo_repo.create_arquivo(
                        nome_arquivo=file_info['original_filename'],
                        path_armazenamento=file_info['file_path'],
                        tipo_arquivo=file_info['content_type'],
                        tamanho_bytes=file_info['file_size'],
                        contrato_id=contrato_id
                    )
                    # Vincula o ID do arquivo ao contrato
                    await self.arquivo_repo.link_arquivo_to_contrato(arquivo_data['id'], contrato_id)
        
        # Retorna o contrato completo com JOINs
        contrato_response = Contrato.model_validate(new_contrato_data)

        # Envio de emails de notificação
        try:
            await self._send_contract_assignment_email(
                contrato_data=new_contrato_data,
                fiscal_id=contrato_create.fiscal_id,
                gestor_id=contrato_create.gestor_id,
                is_update=False
            )
        except Exception as e:
            # Log do erro, mas não falha a criação do contrato
            logger.warning(f"Erro ao enviar emails de notificação para contrato {contrato_id}: {e}")

        return contrato_response

    async def get_contrato_by_id(self, contrato_id: int, user_context: Optional[Dict] = None) -> Optional[Contrato]:
        contrato_data = await self.contrato_repo.find_contrato_by_id(contrato_id, user_context=user_context)
        if contrato_data:
            return Contrato.model_validate(contrato_data)
        return None

    async def get_all_contratos(self, page: int, per_page: int, filters: Optional[Dict] = None, user_context: Optional[Dict] = None) -> ContratoPaginated:
        offset = (page - 1) * per_page
        contratos_data, total_items = await self.contrato_repo.get_all_contratos(
            filters=filters,
            limit=per_page,
            offset=offset,
            user_context=user_context
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
        documento_contrato: Optional[List[UploadFile]] = None
    ) -> Optional[Contrato]:
        """
        Atualiza um contrato existente, incluindo upload de múltiplos arquivos opcionais.
        """

        try:
            # Verifica se o contrato existe
            existing_contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
            if not existing_contrato:
                return None
            
            # Se está atualizando o número do contrato, verifica se já existe
            if hasattr(contrato_update, 'nr_contrato') and contrato_update.nr_contrato:
                if await self.contrato_repo.exists_nr_contrato(contrato_update.nr_contrato, exclude_id=contrato_id):
                    next_available = await self.contrato_repo.get_next_available_nr_contrato()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, 
                        detail=f"Já existe um contrato ativo com o número '{contrato_update.nr_contrato}'. Sugestão: use o número '{next_available}'."
                    )

            # Processa arquivos se fornecidos
            if documento_contrato and any(file.filename for file in documento_contrato if file):
                # Filtra apenas arquivos válidos
                valid_files = [file for file in documento_contrato if file and file.filename and file.filename.strip()]

                if valid_files:
                    # Salva os novos arquivos
                    saved_files = await self.file_service.save_multiple_upload_files(contrato_id, valid_files)

                    # Salva cada arquivo no banco de dados
                    for file_info in saved_files:
                        arquivo_data = await self.arquivo_repo.create_arquivo(
                            nome_arquivo=file_info['original_filename'],
                            path_armazenamento=file_info['file_path'],
                            tipo_arquivo=file_info['content_type'],
                            tamanho_bytes=file_info['file_size'],
                            contrato_id=contrato_id
                        )
                        # Vincula o ID do arquivo ao contrato
                        await self.arquivo_repo.link_arquivo_to_contrato(arquivo_data['id'], contrato_id)

            # Executa a atualização no banco (método correto)
            updated_contrato = await self.contrato_repo.update_contrato(contrato_id, contrato_update)

            return updated_contrato
            
        except Exception as e:
            logging.error(f"Erro ao atualizar contrato {contrato_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno ao atualizar contrato: {str(e)}"
            )

    async def delete_contrato(self, contrato_id: int) -> bool:
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
        return await self.contrato_repo.delete_contrato(contrato_id)

    # Métodos para gerenciamento de arquivos do contrato
    async def get_arquivos_contrato(self, contrato_id: int) -> List[Dict]:
        """Lista todos os arquivos de um contrato específico"""
        # Verifica se o contrato existe
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if not contrato:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado"
            )

        arquivos = await self.contrato_repo.get_arquivos_contrato(contrato_id)
        total_arquivos = await self.contrato_repo.count_arquivos_contrato(contrato_id)

        return {
            "arquivos": arquivos,
            "total_arquivos": total_arquivos,
            "contrato_id": contrato_id
        }

    async def get_arquivo_contrato(self, contrato_id: int, arquivo_id: int) -> Optional[Dict]:
        """Obtém um arquivo específico de um contrato"""
        # Verifica se o contrato existe
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if not contrato:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado"
            )

        arquivo = await self.contrato_repo.get_arquivo_by_id(arquivo_id, contrato_id)
        if not arquivo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo não encontrado neste contrato"
            )

        return arquivo

    async def delete_arquivo_contrato(self, contrato_id: int, arquivo_id: int) -> bool:
        """Remove um arquivo específico de um contrato"""
        # Verifica se o contrato existe
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if not contrato:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado"
            )

        # Busca o arquivo para verificar se existe e obter o path
        arquivo = await self.contrato_repo.get_arquivo_by_id(arquivo_id, contrato_id)
        if not arquivo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo não encontrado neste contrato"
            )

        try:
            # Remove o arquivo do banco de dados
            deleted = await self.contrato_repo.delete_arquivo(arquivo_id, contrato_id)

            if deleted:
                # Remove o arquivo físico do sistema de arquivos
                await self.file_service.delete_file(arquivo['path_armazenamento'])

            return deleted

        except Exception as e:
            logging.error(f"Erro ao deletar arquivo {arquivo_id} do contrato {contrato_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno ao deletar arquivo: {str(e)}"
            )