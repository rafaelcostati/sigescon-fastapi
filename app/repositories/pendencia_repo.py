# app/repositories/pendencia_repo.py
import asyncpg
from typing import List, Dict
from app.schemas.pendencia_schema import PendenciaCreate

class PendenciaRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_pendencia(self, contrato_id: int, pendencia: PendenciaCreate) -> Dict:
        # Usar descricao como titulo se titulo não for fornecido (compatibilidade com frontend)
        titulo = pendencia.titulo or pendencia.descricao
        if not titulo:
            raise ValueError("Título ou descrição deve ser fornecido")

        query = """
            INSERT INTO pendenciarelatorio (contrato_id, titulo, descricao, data_prazo, status_pendencia_id, criado_por_usuario_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        new_pendencia_id = await self.conn.fetchval(
            query,
            contrato_id,
            titulo,
            pendencia.descricao,
            pendencia.data_prazo,
            pendencia.status_pendencia_id,
            pendencia.criado_por_usuario_id
        )
        return await self.get_pendencia_by_id(new_pendencia_id)

    async def get_pendencias_by_contrato_id(self, contrato_id: int) -> List[Dict]:
        query = """
            SELECT
                p.*,
                s.nome as status_nome,
                u.nome as criado_por_nome
            FROM pendenciarelatorio p
            LEFT JOIN statuspendencia s ON p.status_pendencia_id = s.id
            LEFT JOIN usuario u ON p.criado_por_usuario_id = u.id
            WHERE p.contrato_id = $1 AND p.ativo = TRUE
            ORDER BY p.data_prazo DESC
        """
        pendencias = await self.conn.fetch(query, contrato_id)
        return [dict(p) for p in pendencias]

    async def get_pendencia_by_id(self, pendencia_id: int) -> Dict:
        # Função auxiliar para buscar uma pendência com dados completos após a criação
        query = """
            SELECT
                p.*,
                s.nome as status_nome,
                u.nome as criado_por_nome
            FROM pendenciarelatorio p
            LEFT JOIN statuspendencia s ON p.status_pendencia_id = s.id
            LEFT JOIN usuario u ON p.criado_por_usuario_id = u.id
            WHERE p.id = $1 AND p.ativo = TRUE
        """
        pendencia = await self.conn.fetchrow(query, pendencia_id)
        return dict(pendencia) if pendencia else None

    async def update_pendencia_status(self, pendencia_id: int, status_id: int):
        """Atualiza o status de uma pendência (ex: para 'Concluída')."""
        query = "UPDATE pendenciarelatorio SET status_pendencia_id = $1, updated_at = NOW() WHERE id = $2"
        await self.conn.execute(query, status_id, pendencia_id)
        
    async def get_due_pendencias(self) -> List[Dict]:
        """Busca todas as pendências com status 'Pendente'."""
        query = """
            SELECT 
                p.id, p.descricao, p.data_prazo,
                c.nr_contrato,
                u.nome as fiscal_nome, u.email as fiscal_email
            FROM pendenciarelatorio p
            JOIN statuspendencia sp ON p.status_pendencia_id = sp.id
            JOIN contrato c ON p.contrato_id = c.id
            JOIN usuario u ON c.fiscal_id = u.id
            WHERE sp.nome = 'Pendente' AND c.ativo = TRUE
        """
        records = await self.conn.fetch(query)
        return [dict(r) for r in records]
