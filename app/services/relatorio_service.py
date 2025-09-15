# app/services/relatorio_service.py
from typing import List, Optional
from fastapi import HTTPException, status, UploadFile

# Repositórios
from app.repositories.relatorio_repo import RelatorioRepository
from app.repositories.arquivo_repo import ArquivoRepository
from app.repositories.pendencia_repo import PendenciaRepository
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.status_relatorio_repo import StatusRelatorioRepository
from app.repositories.status_pendencia_repo import StatusPendenciaRepository
from app.repositories.usuario_repo import UsuarioRepository

# Services
from app.services.file_service import FileService

# Schemas
from app.schemas.relatorio_schema import Relatorio, RelatorioCreate, RelatorioAnalise
from app.schemas.usuario_schema import Usuario

class RelatorioService:
    def __init__(self,
                 relatorio_repo: RelatorioRepository,
                 arquivo_repo: ArquivoRepository,
                 pendencia_repo: PendenciaRepository,
                 contrato_repo: ContratoRepository,
                 status_relatorio_repo: StatusRelatorioRepository,
                 status_pendencia_repo: StatusPendenciaRepository,
                 usuario_repo: UsuarioRepository,
                 file_service: FileService):
        self.relatorio_repo = relatorio_repo
        self.arquivo_repo = arquivo_repo
        self.pendencia_repo = pendencia_repo
        self.contrato_repo = contrato_repo
        self.status_relatorio_repo = status_relatorio_repo
        self.status_pendencia_repo = status_pendencia_repo
        self.usuario_repo = usuario_repo
        self.file_service = file_service

    async def get_relatorios_by_contrato_id(self, contrato_id: int) -> List[Relatorio]:
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
        
        relatorios_data = await self.relatorio_repo.get_relatorios_by_contrato_id(contrato_id)
        return [Relatorio.model_validate(r) for r in relatorios_data]

    async def submit_relatorio(self, contrato_id: int, relatorio_data: RelatorioCreate, file: UploadFile, current_user: Usuario) -> Relatorio:
        # Validação de permissão: fiscal só pode submeter para seu próprio contrato
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if not contrato:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
        
        # Um admin pode submeter por qualquer um, mas o fiscal só por ele mesmo.
        if "Administrador" not in [p['nome'] for p in await self.usuario_repo.get_all_users() if p['id'] == current_user.perfil_id] and contrato['fiscal_id'] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: Você não é o fiscal deste contrato.")

        # Validação de IDs
        if not await self.pendencia_repo.get_pendencia_by_id(relatorio_data.pendencia_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pendência não encontrada")

        # Processa o upload do ficheiro
        nome_original, path, tamanho = await self.file_service.save_upload_file(contrato_id, file)

        # Cria o registo do ficheiro
        arquivo_criado = await self.arquivo_repo.create_arquivo(
            nome_arquivo=nome_original,
            path_armazenamento=path,
            tipo_arquivo=file.content_type,
            tamanho_bytes=tamanho,
            contrato_id=contrato_id
        )

        # Obtém IDs de status necessários
        status_relatorio_pendente = next(s for s in await self.status_relatorio_repo.get_all() if s['nome'] == 'Pendente de Análise')
        status_pendencia_concluida = next(s for s in await self.status_pendencia_repo.get_all() if s['nome'] == 'Concluída')

        # Cria o registo do relatório
        novo_relatorio_data = await self.relatorio_repo.create_relatorio(
            contrato_id=contrato_id,
            arquivo_id=arquivo_criado['id'],
            status_id=status_relatorio_pendente['id'],
            data=relatorio_data.model_dump()
        )

        # Atualiza o status da pendência para "Concluída"
        await self.pendencia_repo.update_pendencia_status(relatorio_data.pendencia_id, status_pendencia_concluida['id'])

        return Relatorio.model_validate(novo_relatorio_data)

    async def analisar_relatorio(self, relatorio_id: int, analise_data: RelatorioAnalise) -> Relatorio:
        if not await self.relatorio_repo.get_relatorio_by_id(relatorio_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não encontrado")
        
        if not await self.usuario_repo.get_user_by_id(analise_data.aprovador_usuario_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário aprovador não encontrado")
            
        if not await self.status_relatorio_repo.get_by_id(analise_data.status_id):
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de relatório não encontrado")

        relatorio_atualizado = await self.relatorio_repo.analise_relatorio(relatorio_id, analise_data.model_dump())
        
        # Lógica de notificação por e-mail pode ser adicionada aqui
        
        return Relatorio.model_validate(relatorio_atualizado)