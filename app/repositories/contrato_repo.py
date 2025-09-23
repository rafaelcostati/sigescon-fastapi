# app/repositories/contrato_repo.py
import asyncpg
import logging
from typing import List, Optional, Dict, Tuple

from app.schemas.contrato_schema import ContratoCreate, ContratoUpdate

logger = logging.getLogger(__name__)

class ContratoRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_contrato(self, contrato: ContratoCreate) -> Dict:
        # Usar campos específicos para evitar problemas de tipo
        query = """
            INSERT INTO contrato (
                nr_contrato, objeto, data_inicio, data_fim, contratado_id,
                modalidade_id, status_id, gestor_id, fiscal_id,
                valor_anual, valor_global, base_legal, termos_contratuais,
                fiscal_substituto_id, pae, doe, data_doe
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            RETURNING id
        """

        # Converter tipos explicitamente para evitar erros de tipo
        new_contrato_id = await self.conn.fetchval(
            query,
            str(contrato.nr_contrato),  # Garantir que é string
            str(contrato.objeto),  # Garantir que é string
            contrato.data_inicio,
            contrato.data_fim,
            int(contrato.contratado_id),  # Garantir que é inteiro
            int(contrato.modalidade_id),  # Garantir que é inteiro
            int(contrato.status_id),  # Garantir que é inteiro
            int(contrato.gestor_id),  # Garantir que é inteiro
            int(contrato.fiscal_id),  # Garantir que é inteiro
            float(contrato.valor_anual) if contrato.valor_anual is not None else None,
            float(contrato.valor_global) if contrato.valor_global is not None else None,
            str(contrato.base_legal) if contrato.base_legal is not None else None,
            str(contrato.termos_contratuais) if contrato.termos_contratuais is not None else None,
            int(contrato.fiscal_substituto_id) if contrato.fiscal_substituto_id is not None else None,
            str(contrato.pae) if contrato.pae is not None else None,
            str(contrato.doe) if contrato.doe is not None else None,
            contrato.data_doe
        )
        return await self.find_contrato_by_id(new_contrato_id)


    # --- QUERY CORRIGIDA ---
    async def find_contrato_by_id(self, contrato_id: int, user_context: Optional[Dict] = None) -> Optional[Dict]:
        # Garante que contrato_id seja um inteiro
        contrato_id = int(contrato_id)
        
        query = """
            SELECT
                c.*,
                ct.nome AS contratado_nome,
                m.nome AS modalidade_nome,
                s.nome AS status_nome,
                gestor.nome AS gestor_nome,
                fiscal.nome AS fiscal_nome,
                fiscal_sub.nome AS fiscal_substituto_nome
            FROM contrato c
            LEFT JOIN contratado ct ON c.contratado_id = ct.id
            LEFT JOIN modalidade m ON c.modalidade_id = m.id
            LEFT JOIN status s ON c.status_id = s.id
            LEFT JOIN usuario gestor ON c.gestor_id = gestor.id
            LEFT JOIN usuario fiscal ON c.fiscal_id = fiscal.id
            LEFT JOIN usuario fiscal_sub ON c.fiscal_substituto_id = fiscal_sub.id
            WHERE c.id = $1 AND c.ativo = TRUE
        """
        params = [contrato_id]

        # Aplicar isolamento por perfil
        if user_context:
            usuario_id = user_context.get('usuario_id')
            perfil_ativo = user_context.get('perfil_ativo_nome')
            
            # Garante que usuario_id seja um inteiro
            if usuario_id is not None:
                usuario_id = int(usuario_id)
            
            if perfil_ativo == 'Fiscal' and usuario_id is not None:
                # Fiscal vê apenas contratos onde é fiscal ou fiscal substituto
                query += " AND (c.fiscal_id = $2 OR c.fiscal_substituto_id = $2)"
                params.append(usuario_id)
            elif perfil_ativo == 'Gestor' and usuario_id is not None:
                # Gestor vê apenas contratos onde é gestor
                query += " AND c.gestor_id = $2"
                params.append(usuario_id)
            # Administrador vê todos (sem filtro adicional)

        contrato = await self.conn.fetchrow(query, *params)
        return dict(contrato) if contrato else None


    async def get_all_contratos(
        self,
        filters: Optional[Dict] = None,
        order_by: str = 'c.data_fim DESC',
        limit: int = 10,
        offset: int = 0,
        user_context: Optional[Dict] = None
    ) -> Tuple[List[Dict], int]:
        
        base_query = """
            FROM contrato c
            LEFT JOIN contratado ct ON c.contratado_id = ct.id
            LEFT JOIN modalidade m ON c.modalidade_id = m.id
            LEFT JOIN status s ON c.status_id = s.id
        """
        where_clauses = ["c.ativo = TRUE"]
        params = []
        param_idx = 1

        # Aplicar isolamento por perfil
        if user_context:
            usuario_id = user_context.get('usuario_id')
            perfil_ativo = user_context.get('perfil_ativo_nome')

            if perfil_ativo == 'Fiscal':
                # Fiscal vê apenas contratos onde é fiscal ou fiscal substituto
                where_clauses.append(f"(c.fiscal_id = ${param_idx} OR c.fiscal_substituto_id = ${param_idx})")
                params.append(usuario_id)
                param_idx += 1
            elif perfil_ativo == 'Gestor':
                # Gestor vê apenas contratos onde é gestor
                where_clauses.append(f"c.gestor_id = ${param_idx}")
                params.append(usuario_id)
                param_idx += 1
            # Administrador vê todos (sem filtro adicional)

        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                column_map = {'gestor_id': 'c.gestor_id', 'fiscal_id': 'c.fiscal_id', 'contratado_id': 'c.contratado_id', 'modalidade_id': 'c.modalidade_id', 'status_id': 'c.status_id', 'ano': 'EXTRACT(YEAR FROM c.data_inicio)'}
                if key in column_map:
                    where_clauses.append(f"{column_map[key]} = ${param_idx}")
                    params.append(value)
                    param_idx += 1
                elif key in ['objeto', 'nr_contrato', 'pae']:
                    where_clauses.append(f"c.{key} ILIKE ${param_idx}")
                    params.append(f"%{value}%")
                    param_idx += 1
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        count_query = f"SELECT COUNT(c.id) AS total {base_query}{where_sql}"
        total_items = await self.conn.fetchval(count_query, *params)
        data_query = f"""
            SELECT
                c.id, c.nr_contrato, c.objeto, c.data_fim,
                c.fiscal_id, c.gestor_id,
                ct.nome as contratado_nome,
                s.nome as status_nome,
                fiscal.nome as fiscal_nome,
                gestor.nome as gestor_nome
            {base_query}
            LEFT JOIN usuario fiscal ON c.fiscal_id = fiscal.id
            LEFT JOIN usuario gestor ON c.gestor_id = gestor.id
            {where_sql}
            ORDER BY {order_by}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        paginated_params = params + [limit, offset]
        contratos = await self.conn.fetch(data_query, *paginated_params)
        return [dict(c) for c in contratos], total_items if total_items is not None else 0


    async def update_contrato(self, contrato_id: int, contrato: ContratoUpdate) -> Optional[Dict]:
        update_data = contrato.model_dump(exclude_unset=True)
        if not update_data:
            return await self.find_contrato_by_id(contrato_id)

        # Construir UPDATE de forma mais segura com parâmetros explícitos
        set_clauses = []
        values = []
        param_index = 1

        # Mapear campos para garantir tipos corretos
        for field, value in update_data.items():
            set_clauses.append(f"{field} = ${param_index}")

            # Conversões explícitas para garantir tipos corretos
            if field in ['contratado_id', 'modalidade_id', 'status_id', 'gestor_id', 'fiscal_id', 'fiscal_substituto_id']:
                # Campos ID devem ser inteiros
                values.append(int(value) if value is not None else None)
            elif field in ['nr_contrato', 'objeto', 'base_legal', 'termos_contratuais', 'pae', 'doe', 'documento']:
                # Campos texto devem ser strings
                values.append(str(value) if value is not None else None)
            elif field in ['valor_anual', 'valor_global']:
                # Campos monetários devem ser float
                values.append(float(value) if value is not None else None)
            else:
                # Outros campos mantém o tipo original
                values.append(value)

            param_index += 1

        # Adicionar contrato_id como último parâmetro para o WHERE
        values.append(contrato_id)
        where_param = param_index

        query = f"""
            UPDATE contrato
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE id = ${where_param} AND ativo = TRUE
            RETURNING id
        """

        updated_id = await self.conn.fetchval(query, *values)
        if updated_id:
            return await self.find_contrato_by_id(updated_id)
        return None


    async def delete_contrato(self, contrato_id: int) -> bool:
        query = "UPDATE contrato SET ativo = FALSE, updated_at = NOW() WHERE id = $1 AND ativo = TRUE"
        status = await self.conn.execute(query, contrato_id)
        return status.endswith('1')
    
    async def get_by_id(self, contrato_id: int) -> Optional[Dict]:
        """Alias para find_contrato_by_id para manter consistência com outros repositories"""
        return await self.find_contrato_by_id(contrato_id)
    
    async def get_contrato_by_id(self, contrato_id: int) -> Optional[Dict]:
        """Alias adicional para compatibilidade"""
        return await self.find_contrato_by_id(contrato_id)

    # Métodos para gerenciamento de arquivos do contrato
    async def get_arquivos_contrato(self, contrato_id: int) -> List[Dict]:
        """Busca todos os arquivos de um contrato específico"""
        query = """
            SELECT
                id,
                nome_arquivo,
                tipo_mime as tipo_arquivo,
                tamanho_bytes,
                contrato_id,
                created_at::text as created_at
            FROM arquivo
            WHERE contrato_id = $1
            ORDER BY created_at DESC
        """
        rows = await self.conn.fetch(query, contrato_id)
        return [dict(row) for row in rows]

    async def get_arquivo_by_id(self, arquivo_id: int, contrato_id: int) -> Optional[Dict]:
        """Busca um arquivo específico de um contrato"""
        query = """
            SELECT
                id,
                nome_arquivo,
                caminho_arquivo as path_armazenamento,
                tipo_mime as tipo_arquivo,
                tamanho_bytes,
                contrato_id,
                created_at::text as created_at
            FROM arquivo
            WHERE id = $1 AND contrato_id = $2
        """
        row = await self.conn.fetchrow(query, arquivo_id, contrato_id)
        return dict(row) if row else None

    async def delete_arquivo(self, arquivo_id: int, contrato_id: int) -> bool:
        """Remove um arquivo específico de um contrato"""
        query = "DELETE FROM arquivo WHERE id = $1 AND contrato_id = $2"
        status = await self.conn.execute(query, arquivo_id, contrato_id)
        return status.endswith('1')

    async def count_arquivos_contrato(self, contrato_id: int) -> int:
        """Conta o número total de arquivos de um contrato"""
        query = "SELECT COUNT(*) FROM arquivo WHERE contrato_id = $1"
        return await self.conn.fetchval(query, contrato_id)
    
    async def exists_nr_contrato(self, nr_contrato: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica se um número de contrato já existe (apenas contratos ativos)"""
        # Garante que nr_contrato seja sempre uma string
        nr_contrato_str = str(nr_contrato)
        
        if exclude_id:
            query = "SELECT EXISTS(SELECT 1 FROM contrato WHERE nr_contrato = $1 AND ativo = TRUE AND id != $2)"
            return await self.conn.fetchval(query, nr_contrato_str, exclude_id)
        else:
            query = "SELECT EXISTS(SELECT 1 FROM contrato WHERE nr_contrato = $1 AND ativo = TRUE)"
            return await self.conn.fetchval(query, nr_contrato_str)
    
    async def get_next_available_nr_contrato(self) -> str:
        """Retorna o próximo número de contrato disponível"""
        query = """
            SELECT COALESCE(MAX(CAST(nr_contrato AS INTEGER)), 0) + 1
            FROM contrato 
            WHERE ativo = TRUE 
            AND nr_contrato ~ '^[0-9]+$'
        """
        next_number = await self.conn.fetchval(query)
        return str(next_number)