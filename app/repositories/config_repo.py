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

    # ==================== Modelo de Relatório ====================
    
    async def get_modelo_relatorio_info(self) -> Optional[Dict]:
        """
        Busca as informações do modelo de relatório ativo
        Retorna dict com arquivo_id, nome_original e ativo, ou None se não houver modelo
        """
        configs = await self.conn.fetch("""
            SELECT chave, valor
            FROM configuracao_sistema
            WHERE chave IN ('modelo_relatorio_arquivo_id', 
                          'modelo_relatorio_nome_original',
                          'modelo_relatorio_ativo')
        """)
        
        if not configs:
            return None
        
        config_dict = {c['chave']: c['valor'] for c in configs}
        
        # Verifica se está ativo e tem arquivo_id
        ativo = config_dict.get('modelo_relatorio_ativo', 'false').lower() == 'true'
        arquivo_id = config_dict.get('modelo_relatorio_arquivo_id')
        
        if not ativo or not arquivo_id:
            return None
        
        try:
            return {
                'arquivo_id': int(arquivo_id),
                'nome_original': config_dict.get('modelo_relatorio_nome_original', 'modelo_relatorio.pdf'),
                'ativo': True
            }
        except (ValueError, TypeError):
            return None
    
    async def set_modelo_relatorio(self, arquivo_id: int, nome_original: str) -> None:
        """
        Configura um novo modelo de relatório
        """
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = $1, updated_at = NOW()
            WHERE chave = 'modelo_relatorio_arquivo_id'
        """, str(arquivo_id))
        
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = $1, updated_at = NOW()
            WHERE chave = 'modelo_relatorio_nome_original'
        """, nome_original)
        
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = 'true', updated_at = NOW()
            WHERE chave = 'modelo_relatorio_ativo'
        """)
    
    async def remove_modelo_relatorio(self) -> Optional[int]:
        """
        Remove o modelo de relatório ativo
        Retorna o arquivo_id do modelo anterior para deleção física
        """
        # Buscar o arquivo_id atual antes de remover
        config = await self.get_config('modelo_relatorio_arquivo_id')
        arquivo_id = None
        
        if config and config['valor']:
            try:
                arquivo_id = int(config['valor'])
            except (ValueError, TypeError):
                pass
        
        # Desativar o modelo
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = 'false', updated_at = NOW()
            WHERE chave = 'modelo_relatorio_ativo'
        """)
        
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = NULL, updated_at = NOW()
            WHERE chave = 'modelo_relatorio_arquivo_id'
        """)
        
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = NULL, updated_at = NOW()
            WHERE chave = 'modelo_relatorio_nome_original'
        """)
        
        return arquivo_id
    
    # ==================== Alertas de Vencimento ====================
    
    async def get_alertas_vencimento_config(self) -> Dict:
        """
        Busca todas as configurações de alertas de vencimento
        Retorna dict com todas as configs ou valores padrão
        """
        configs = await self.conn.fetch("""
            SELECT chave, valor
            FROM configuracao_sistema
            WHERE chave LIKE 'alertas_vencimento%'
        """)
        
        config_dict = {c['chave']: c['valor'] for c in configs}
        
        # Valores padrão caso não existam
        return {
            'ativo': config_dict.get('alertas_vencimento_ativo', 'true').lower() == 'true',
            'dias_antes': int(config_dict.get('alertas_vencimento_dias_antes', '90')),
            'periodicidade_dias': int(config_dict.get('alertas_vencimento_periodicidade_dias', '30')),
            'perfis_destino': config_dict.get('alertas_vencimento_perfis_destino', '["Administrador"]'),
            'hora_envio': config_dict.get('alertas_vencimento_hora_envio', '10:00')
        }
    
    async def update_alertas_vencimento_ativo(self, ativo: bool) -> None:
        """Ativa ou desativa os alertas de vencimento"""
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = $1, updated_at = NOW()
            WHERE chave = 'alertas_vencimento_ativo'
        """, 'true' if ativo else 'false')
    
    async def update_alertas_vencimento_dias_antes(self, dias: int) -> None:
        """Atualiza quantos dias antes do vencimento começar alertas"""
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = $1, updated_at = NOW()
            WHERE chave = 'alertas_vencimento_dias_antes'
        """, str(dias))
    
    async def update_alertas_vencimento_periodicidade(self, dias: int) -> None:
        """Atualiza periodicidade de reenvio dos alertas"""
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = $1, updated_at = NOW()
            WHERE chave = 'alertas_vencimento_periodicidade_dias'
        """, str(dias))
    
    async def update_alertas_vencimento_perfis(self, perfis: list) -> None:
        """Atualiza perfis que receberão os alertas"""
        import json
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = $1, updated_at = NOW()
            WHERE chave = 'alertas_vencimento_perfis_destino'
        """, json.dumps(perfis))
    
    async def update_alertas_vencimento_hora(self, hora: str) -> None:
        """Atualiza hora de envio dos alertas"""
        await self.conn.execute("""
            UPDATE configuracao_sistema
            SET valor = $1, updated_at = NOW()
            WHERE chave = 'alertas_vencimento_hora_envio'
        """, hora)
    
    async def update_alertas_vencimento_completo(
        self,
        ativo: bool,
        dias_antes: int,
        periodicidade_dias: int,
        perfis_destino: list,
        hora_envio: str
    ) -> None:
        """Atualiza todas as configurações de alertas de vencimento de uma vez"""
        await self.update_alertas_vencimento_ativo(ativo)
        await self.update_alertas_vencimento_dias_antes(dias_antes)
        await self.update_alertas_vencimento_periodicidade(periodicidade_dias)
        await self.update_alertas_vencimento_perfis(perfis_destino)
        await self.update_alertas_vencimento_hora(hora_envio)

    # ==================== Escalonamento de Pendências ====================

    async def get_escalonamento_ativo(self) -> bool:
        """Retorna se o sistema de escalonamento está ativo"""
        config = await self.get_config('escalonamento_ativo')
        if config:
            return config['valor'].lower() == 'true'
        return True  # Ativo por padrão

    async def get_escalonamento_dias_gestor(self) -> int:
        """Retorna dias após vencimento para notificar gestor"""
        config = await self.get_config('escalonamento_gestor_dias')
        if config:
            try:
                return int(config['valor'])
            except (ValueError, TypeError):
                return 7  # Padrão: 7 dias
        return 7

    async def get_escalonamento_dias_admin(self) -> int:
        """Retorna dias após vencimento para notificar admin"""
        config = await self.get_config('escalonamento_admin_dias')
        if config:
            try:
                return int(config['valor'])
            except (ValueError, TypeError):
                return 14  # Padrão: 14 dias
        return 14

    async def get_escalonamento_config(self) -> Dict:
        """Retorna todas as configurações de escalonamento"""
        return {
            'ativo': await self.get_escalonamento_ativo(),
            'dias_gestor': await self.get_escalonamento_dias_gestor(),
            'dias_admin': await self.get_escalonamento_dias_admin()
        }

    async def update_escalonamento_ativo(self, ativo: bool) -> None:
        """Atualiza se o escalonamento está ativo"""
        await self.update_config('escalonamento_ativo', str(ativo).lower())

    async def update_escalonamento_dias_gestor(self, dias: int) -> None:
        """Atualiza dias para notificar gestor"""
        await self.update_config('escalonamento_gestor_dias', str(dias))

    async def update_escalonamento_dias_admin(self, dias: int) -> None:
        """Atualiza dias para notificar admin"""
        await self.update_config('escalonamento_admin_dias', str(dias))

    async def update_escalonamento_completo(
        self,
        ativo: bool,
        dias_gestor: int,
        dias_admin: int
    ) -> None:
        """Atualiza todas as configurações de escalonamento de uma vez"""
        await self.update_escalonamento_ativo(ativo)
        await self.update_escalonamento_dias_gestor(dias_gestor)
        await self.update_escalonamento_dias_admin(dias_admin)
