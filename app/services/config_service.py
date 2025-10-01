# app/services/config_service.py
from typing import List, Optional
from fastapi import HTTPException, status, UploadFile, Request
import logging
from app.repositories.config_repo import ConfigRepository
from app.repositories.arquivo_repo import ArquivoRepository
from app.services.file_service import FileService
from app.services.audit_integration import audit_atualizar_configuracao
from app.schemas.config_schema import Config, ConfigUpdate, ConfigCreate, ModeloRelatorioInfo, ModeloRelatorioResponse, AlertasVencimentoConfig, AlertasVencimentoConfigUpdate
from app.schemas.usuario_schema import Usuario
import os
import json

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, config_repo: ConfigRepository):
        self.config_repo = config_repo

    async def get_config(self, chave: str) -> Config:
        """Busca uma configuração pela chave"""
        config_data = await self.config_repo.get_config(chave)
        if not config_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuração '{chave}' não encontrada"
            )
        return Config.model_validate(config_data)

    async def get_all_configs(self) -> List[Config]:
        """Busca todas as configurações"""
        configs_data = await self.config_repo.get_all_configs()
        return [Config.model_validate(c) for c in configs_data]

    async def update_config(self, chave: str, config_update: ConfigUpdate) -> Config:
        """Atualiza o valor de uma configuração"""
        # Verifica se a configuração existe
        existing_config = await self.config_repo.get_config(chave)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuração '{chave}' não encontrada"
            )

        # Valida o valor baseado no tipo
        tipo = existing_config['tipo']
        valor = config_update.valor

        try:
            if tipo == 'integer':
                int(valor)
            elif tipo == 'boolean':
                if valor.lower() not in ['true', 'false', '1', '0']:
                    raise ValueError("Valor booleano inválido")
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Valor inválido para tipo '{tipo}'"
            )

        # Atualiza a configuração
        updated_config = await self.config_repo.update_config(chave, valor)
        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao atualizar configuração"
            )

        return Config.model_validate(updated_config)

    async def get_pendencias_intervalo_dias(self) -> int:
        """Retorna o intervalo de dias configurado para pendências automáticas"""
        return await self.config_repo.get_pendencias_intervalo_dias()

    async def update_pendencias_intervalo_dias(
        self,
        intervalo_dias: int,
        current_user: Optional[Usuario] = None,
        request: Optional[Request] = None
    ) -> Config:
        """Atualiza o intervalo de dias para pendências automáticas"""
        if intervalo_dias < 1 or intervalo_dias > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Intervalo deve estar entre 1 e 365 dias"
            )

        # Busca valor anterior
        valor_anterior = await self.config_repo.get_pendencias_intervalo_dias()

        config_update = ConfigUpdate(valor=str(intervalo_dias))
        updated = await self.update_config('pendencias_automaticas_intervalo_dias', config_update)

        # Log de auditoria
        if current_user:
            try:
                await audit_atualizar_configuracao(
                    conn=self.config_repo.conn,
                    request=request,
                    usuario=current_user,
                    chave_config='pendencias_automaticas_intervalo_dias',
                    valor_anterior=valor_anterior,
                    valor_novo=intervalo_dias,
                    perfil_usado=current_user.perfil_ativo if hasattr(current_user, 'perfil_ativo') else None
                )
            except Exception as e:
                logger.warning(f"Erro ao criar log de auditoria para config pendencias_automaticas_intervalo_dias: {e}")

        return updated

    async def get_lembretes_config(self) -> dict:
        """Retorna as configurações de lembretes de pendências"""
        dias_antes_inicio = await self.config_repo.get_lembretes_dias_antes_inicio()
        intervalo_dias = await self.config_repo.get_lembretes_intervalo_dias()
        return {
            "dias_antes_vencimento_inicio": dias_antes_inicio,
            "intervalo_dias_lembrete": intervalo_dias
        }

    async def update_lembretes_config(self, dias_antes_inicio: int, intervalo_dias: int) -> dict:
        """Atualiza as configurações de lembretes de pendências"""
        # Validações
        if dias_antes_inicio < 1 or dias_antes_inicio > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dias antes do vencimento deve estar entre 1 e 90 dias"
            )
        
        if intervalo_dias < 1 or intervalo_dias > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Intervalo entre lembretes deve estar entre 1 e 30 dias"
            )

        # Atualiza as configurações
        await self.update_config('lembretes_dias_antes_vencimento_inicio', ConfigUpdate(valor=str(dias_antes_inicio)))
        await self.update_config('lembretes_intervalo_dias', ConfigUpdate(valor=str(intervalo_dias)))

        return {
            "dias_antes_vencimento_inicio": dias_antes_inicio,
            "intervalo_dias_lembrete": intervalo_dias
        }

    # ==================== Modelo de Relatório ====================
    
    async def get_modelo_relatorio_info(self) -> Optional[ModeloRelatorioInfo]:
        """Retorna informações sobre o modelo de relatório ativo"""
        modelo_info = await self.config_repo.get_modelo_relatorio_info()
        if not modelo_info:
            return None
        return ModeloRelatorioInfo(**modelo_info)
    
    async def upload_modelo_relatorio(
        self, 
        file: UploadFile, 
        arquivo_repo: ArquivoRepository,
        file_service: FileService
    ) -> ModeloRelatorioResponse:
        """
        Faz upload de um novo modelo de relatório
        Remove o modelo anterior se existir
        """
        # Valida o tipo de arquivo
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo inválido"
            )
        
        # Valida extensão
        allowed_extensions = {'pdf', 'doc', 'docx', 'odt'}
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de arquivo não permitido. Use: {', '.join(allowed_extensions)}"
            )
        
        try:
            # Remove o modelo anterior se existir
            modelo_anterior = await self.config_repo.get_modelo_relatorio_info()
            if modelo_anterior:
                arquivo_id_anterior = modelo_anterior['arquivo_id']
                # Busca info do arquivo anterior para deletar fisicamente
                arquivo_anterior = await arquivo_repo.get_arquivo_by_id(arquivo_id_anterior)
                if arquivo_anterior:
                    # Deleta arquivo físico
                    if os.path.exists(arquivo_anterior['caminho']):
                        os.remove(arquivo_anterior['caminho'])
                    # Deleta registro do banco
                    await arquivo_repo.delete_arquivo(arquivo_id_anterior)
            
            # Salva o novo arquivo (usa None para indicar que é um arquivo global sem vínculo com contrato)
            # Note: passamos 0 para o file_service apenas para criar o diretório, mas não vinculamos ao contrato
            original_filename, file_path, file_size = await file_service.save_upload_file(0, file)
            
            # Determina o tipo MIME
            mime_types = {
                'pdf': 'application/pdf',
                'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'odt': 'application/vnd.oasis.opendocument.text'
            }
            tipo_mime = mime_types.get(ext, 'application/octet-stream')
            
            # Registra no banco de dados na tabela arquivo com contrato_id = None (arquivo global)
            arquivo = await arquivo_repo.create_arquivo_global(
                nome_arquivo=original_filename,
                path_armazenamento=file_path,
                tipo_arquivo=tipo_mime,
                tamanho_bytes=file_size
            )
            arquivo_id = arquivo['id']
            
            # Atualiza as configurações
            await self.config_repo.set_modelo_relatorio(arquivo_id, original_filename)
            
            return ModeloRelatorioResponse(
                success=True,
                message="Modelo de relatório atualizado com sucesso",
                modelo=ModeloRelatorioInfo(
                    arquivo_id=arquivo_id,
                    nome_original=original_filename,
                    ativo=True
                )
            )
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao fazer upload do modelo: {str(e)}"
            )
    
    async def remove_modelo_relatorio(
        self, 
        arquivo_repo: ArquivoRepository
    ) -> ModeloRelatorioResponse:
        """Remove o modelo de relatório ativo"""
        modelo_info = await self.config_repo.get_modelo_relatorio_info()
        
        if not modelo_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum modelo de relatório ativo"
            )
        
        try:
            arquivo_id = modelo_info['arquivo_id']
            
            # Busca info do arquivo para deletar fisicamente
            arquivo = await arquivo_repo.get_arquivo_by_id(arquivo_id)
            if arquivo:
                # Deleta arquivo físico
                if os.path.exists(arquivo['caminho']):
                    os.remove(arquivo['caminho'])
                # Deleta registro do banco
                await arquivo_repo.delete_arquivo(arquivo_id)
            
            # Remove as configurações
            await self.config_repo.remove_modelo_relatorio()
            
            return ModeloRelatorioResponse(
                success=True,
                message="Modelo de relatório removido com sucesso",
                modelo=None
            )
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao remover modelo: {str(e)}"
            )
    
    # ==================== Alertas de Vencimento ====================
    
    async def get_alertas_vencimento_config(self) -> AlertasVencimentoConfig:
        """Retorna configurações de alertas de vencimento"""
        try:
            print("🔍 DEBUG: Chamando config_repo.get_alertas_vencimento_config()")
            config_data = await self.config_repo.get_alertas_vencimento_config()
            print(f"✅ DEBUG: Dados recebidos do repo: {config_data}")
            
            # Parse perfis_destino de JSON string para lista
            perfis_destino = json.loads(config_data['perfis_destino'])
            print(f"✅ DEBUG: Perfis parseados: {perfis_destino}")
            
            return AlertasVencimentoConfig(
                ativo=config_data['ativo'],
                dias_antes=config_data['dias_antes'],
                periodicidade_dias=config_data['periodicidade_dias'],
                perfis_destino=perfis_destino,
                hora_envio=config_data['hora_envio']
            )
        except Exception as e:
            # Se não encontrou as configurações no banco, retorna valores padrão
            # Isso permite que a aplicação funcione antes da migração ser executada
            print(f"⚠️ DEBUG: Exceção capturada: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return AlertasVencimentoConfig(
                ativo=True,
                dias_antes=90,
                periodicidade_dias=30,
                perfis_destino=['Administrador'],
                hora_envio='10:00'
            )
    
    async def update_alertas_vencimento_config(
        self, 
        config: AlertasVencimentoConfigUpdate
    ) -> AlertasVencimentoConfig:
        """Atualiza configurações de alertas de vencimento"""
        
        # Validações
        if config.dias_antes < 1 or config.dias_antes > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dias antes do vencimento deve estar entre 1 e 365 dias"
            )
        
        if config.periodicidade_dias < 1 or config.periodicidade_dias > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Periodicidade deve estar entre 1 e 90 dias"
            )
        
        # Valida perfis
        perfis_validos = ['Administrador', 'Gestor', 'Fiscal']
        for perfil in config.perfis_destino:
            if perfil not in perfis_validos:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Perfil inválido: {perfil}. Perfis válidos: {', '.join(perfis_validos)}"
                )
        
        if not config.perfis_destino:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deve haver pelo menos um perfil de destino"
            )
        
        # Valida formato de hora (HH:MM)
        try:
            hora_parts = config.hora_envio.split(':')
            if len(hora_parts) != 2:
                raise ValueError()
            hora = int(hora_parts[0])
            minuto = int(hora_parts[1])
            if hora < 0 or hora > 23 or minuto < 0 or minuto > 59:
                raise ValueError()
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de hora inválido. Use HH:MM (ex: 10:00)"
            )
        
        try:
            # Atualiza todas as configurações
            await self.config_repo.update_alertas_vencimento_completo(
                ativo=config.ativo,
                dias_antes=config.dias_antes,
                periodicidade_dias=config.periodicidade_dias,
                perfis_destino=config.perfis_destino,
                hora_envio=config.hora_envio
            )
            
            # Retorna as configurações atualizadas
            return await self.get_alertas_vencimento_config()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao atualizar configurações: {str(e)}"
            )

    # ==================== Escalonamento de Pendências ====================

    async def get_escalonamento_config(self) -> dict:
        """Retorna as configurações de escalonamento de pendências"""
        return await self.config_repo.get_escalonamento_config()

    async def update_escalonamento_config(self, config: 'EscalonamentoConfigUpdate') -> dict:
        """
        Atualiza as configurações de escalonamento de pendências

        Args:
            config: Configurações de escalonamento

        Returns:
            Configurações atualizadas
        """
        # Validações
        if config.dias_gestor < 1 or config.dias_gestor > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dias para notificar gestor deve estar entre 1 e 90"
            )

        if config.dias_admin < 1 or config.dias_admin > 180:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dias para notificar administrador deve estar entre 1 e 180"
            )

        if config.dias_admin <= config.dias_gestor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dias para notificar administrador deve ser maior que dias para notificar gestor"
            )

        try:
            # Atualiza as configurações
            await self.config_repo.update_escalonamento_completo(
                ativo=config.ativo,
                dias_gestor=config.dias_gestor,
                dias_admin=config.dias_admin
            )

            # Retorna as configurações atualizadas
            return await self.get_escalonamento_config()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao atualizar configurações de escalonamento: {str(e)}"
            )
