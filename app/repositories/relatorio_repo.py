# app/repositories/relatorio_repo.py
import asyncpg
from typing import List, Optional, Dict

class RelatorioRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_relatorio(
        self,
        contrato_id: int,
        arquivo_id: int,
        status_id: int,
        data: Dict
    ) -> Dict:
        query = """
            INSERT INTO relatoriofiscal 
                (contrato_id, fiscal_usuario_id, arquivo_id, status_id, 
                 mes_competencia, observacoes_fiscal, pendencia_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        relatorio_id = await self.conn.fetchval(
            query,
            contrato_id,
            data['fiscal_usuario_id'],
            arquivo_id,
            status_id,
            data['mes_competencia'],
            data.get('observacoes_fiscal'),
            data['pendencia_id']
        )
        return await self.get_relatorio_by_id(relatorio_id)

    async def get_relatorios_by_contrato_id(self, contrato_id: int) -> List[Dict]:
        query = """
            SELECT
                rf.*, -- Seleciona todos os campos da tabela relatoriofiscal
                u.nome as enviado_por,
                s.nome as status_relatorio,
                a.nome_arquivo
            FROM relatoriofiscal rf
            LEFT JOIN usuario u ON rf.fiscal_usuario_id = u.id
            LEFT JOIN statusrelatorio s ON rf.status_id = s.id
            LEFT JOIN arquivo a ON rf.arquivo_id = a.id
            WHERE rf.contrato_id = $1 ORDER BY rf.created_at DESC
        """
        records = await self.conn.fetch(query, contrato_id)
        return [dict(r) for r in records]

    async def get_relatorio_by_id(self, relatorio_id: int) -> Optional[Dict]:
        query = """
            SELECT
                rf.*,
                u.nome as enviado_por,
                s.nome as status_relatorio,
                a.nome_arquivo
            FROM relatoriofiscal rf
            LEFT JOIN usuario u ON rf.fiscal_usuario_id = u.id
            LEFT JOIN statusrelatorio s ON rf.status_id = s.id
            LEFT JOIN arquivo a ON rf.arquivo_id = a.id
            WHERE rf.id = $1
        """
        record = await self.conn.fetchrow(query, relatorio_id)
        return dict(record) if record else None

    async def analise_relatorio(self, relatorio_id: int, data: Dict) -> Dict:
        query = """
            UPDATE relatoriofiscal
            SET status_id = $1, aprovador_usuario_id = $2, observacoes_aprovador = $3, data_analise = NOW()
            WHERE id = $4
            RETURNING id
        """
        await self.conn.execute(
            query,
            data['status_id'],
            data['aprovador_usuario_id'],
            data.get('observacoes_aprovador'),
            relatorio_id
        )
        return await self.get_relatorio_by_id(relatorio_id)

    async def get_relatorios_pendentes_analise(self, contrato_id: int) -> List[Dict]:
        """Busca relatórios com status 'Pendente de Análise' para um contrato"""
        query = """
            SELECT
                rf.*,
                u.nome as enviado_por,
                s.nome as status_relatorio,
                a.nome_arquivo,
                p.descricao as pendencia_descricao
            FROM relatoriofiscal rf
            LEFT JOIN usuario u ON rf.fiscal_usuario_id = u.id
            LEFT JOIN statusrelatorio s ON rf.status_id = s.id
            LEFT JOIN arquivo a ON rf.arquivo_id = a.id
            LEFT JOIN pendenciarelatorio p ON rf.pendencia_id = p.id
            WHERE rf.contrato_id = $1 AND s.nome = 'Pendente de Análise'
            ORDER BY rf.created_at DESC
        """
        records = await self.conn.fetch(query, contrato_id)
        return [dict(r) for r in records]

    async def get_relatorios_by_pendencia_id(self, pendencia_id: int) -> List[Dict]:
        """Busca todos os relatórios associados a uma pendência específica"""
        query = """
            SELECT
                rf.*,
                u.nome as enviado_por,
                s.nome as status_relatorio,
                a.nome_arquivo
            FROM relatoriofiscal rf
            LEFT JOIN usuario u ON rf.fiscal_usuario_id = u.id
            LEFT JOIN statusrelatorio s ON rf.status_id = s.id
            LEFT JOIN arquivo a ON rf.arquivo_id = a.id
            WHERE rf.pendencia_id = $1
            ORDER BY rf.created_at DESC
        """
        records = await self.conn.fetch(query, pendencia_id)
        return [dict(r) for r in records]

    async def update_relatorio_arquivo(self, relatorio_id: int, novo_arquivo_id: int, status_id: int) -> None:
        """Atualiza o arquivo de um relatório (para casos de reenvio)"""
        query = """
            UPDATE relatoriofiscal
            SET arquivo_id = $1, status_id = $2, created_at = NOW()
            WHERE id = $3
        """
        await self.conn.execute(query, novo_arquivo_id, status_id, relatorio_id)