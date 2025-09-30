# app/repositories/config_repo.py
import asyncpg
from typing import Optional, Dict, List

class ConfigRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_config(self, chave: str) -> Optional[Dict]:
        """Busca uma configuração pela chave"""
        query = "SELECT * FROM configuracao_sistema WHERE chave = $1"
        config = await self.conn.fetchrow(query, chave)
        return dict(config) if config else None

    async def get_all_configs(self) -> List[Dict]:
        """Busca todas as configurações"""
        query = "SELECT * FROM configuracao_sistema ORDER BY chave"
        configs = await self.conn.fetch(query)
        return [dict(c) for c in configs]

    async def update_config(self, chave: str, valor: str) -> Optional[Dict]:
        """Atualiza o valor de uma configuração"""
        query = """
            UPDATE configuracao_sistema
            SET valor = $1, updated_at = NOW()
            WHERE chave = $2
            RETURNING *
        """
        config = await self.conn.fetchrow(query, valor, chave)
        return dict(config) if config else None

    async def create_config(self, chave: str, valor: str, descricao: str, tipo: str = 'string') -> Dict:
        """Cria uma nova configuração"""
        query = """
            INSERT INTO configuracao_sistema (chave, valor, descricao, tipo)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """
        config = await self.conn.fetchrow(query, chave, valor, descricao, tipo)
        return dict(config)

    async def get_pendencias_intervalo_dias(self) -> int:
        """Busca o intervalo de dias configurado para pendências automáticas"""
        config = await self.get_config('pendencias_automaticas_intervalo_dias')
        if config:
            try:
                return int(config['valor'])
            except (ValueError, TypeError):
                return 60  # Valor padrão
        return 60  # Valor padrão

    async def get_lembretes_dias_antes_inicio(self) -> int:
        """Busca quantos dias antes do vencimento começar a enviar lembretes"""
        config = await self.get_config('lembretes_dias_antes_vencimento_inicio')
        if config:
            try:
                return int(config['valor'])
            except (ValueError, TypeError):
                return 30  # Valor padrão: 30 dias antes
        return 30  # Valor padrão

    async def get_lembretes_intervalo_dias(self) -> int:
        """Busca o intervalo de dias entre lembretes"""
        config = await self.get_config('lembretes_intervalo_dias')
        if config:
            try:
                return int(config['valor'])
            except (ValueError, TypeError):
                return 5  # Valor padrão: a cada 5 dias
        return 5  # Valor padrão
