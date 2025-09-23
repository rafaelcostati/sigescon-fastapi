# app/repositories/arquivo_repo.py
import asyncpg
from typing import Dict, Optional 

class ArquivoRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_arquivo(
        self,
        nome_arquivo: str,
        path_armazenamento: str,
        tipo_arquivo: str,
        tamanho_bytes: int,
        contrato_id: int
    ) -> Dict:
        query = """
            INSERT INTO arquivo (nome_arquivo, caminho_arquivo, tipo_mime, tamanho_bytes, contrato_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, nome_arquivo, caminho_arquivo as path_armazenamento, tipo_mime as tipo_arquivo, tamanho_bytes, contrato_id, ativo, created_at, updated_at
        """
        new_arquivo = await self.conn.fetchrow(
            query, nome_arquivo, path_armazenamento, tipo_arquivo, tamanho_bytes, contrato_id
        )
        return dict(new_arquivo)

    async def link_arquivo_to_contrato(self, arquivo_id: int, contrato_id: int):
        """Define o arquivo como o documento principal do contrato."""
        query = "UPDATE contrato SET documento = $1 WHERE id = $2"
        # Converter arquivo_id para string, pois a coluna documento é VARCHAR
        await self.conn.execute(query, str(arquivo_id), contrato_id)
        
    async def find_arquivo_by_id(self, arquivo_id: int) -> Optional[Dict]:
        """Busca um arquivo pelo seu ID."""
        query = """
            SELECT id, nome_arquivo, caminho_arquivo as path_armazenamento,
                   tipo_mime as tipo_arquivo, tamanho_bytes, contrato_id,
                   ativo, created_at, updated_at
            FROM arquivo WHERE id = $1 AND ativo = TRUE
        """
        record = await self.conn.fetchrow(query, arquivo_id)
        return dict(record) if record else None
