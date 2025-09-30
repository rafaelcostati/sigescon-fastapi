# app/services/config_service.py
from typing import List, Optional
from fastapi import HTTPException, status
from app.repositories.config_repo import ConfigRepository
from app.schemas.config_schema import Config, ConfigUpdate, ConfigCreate

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

    async def update_pendencias_intervalo_dias(self, intervalo_dias: int) -> Config:
        """Atualiza o intervalo de dias para pendências automáticas"""
        if intervalo_dias < 1 or intervalo_dias > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Intervalo deve estar entre 1 e 365 dias"
            )

        config_update = ConfigUpdate(valor=str(intervalo_dias))
        return await self.update_config('pendencias_automaticas_intervalo_dias', config_update)
