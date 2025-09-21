#!/usr/bin/env python3
"""
Script para inspecionar schema do servidor e comparar com local
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings

async def inspect_table_schema(conn, table_name):
    """Inspecciona a estrutura de uma tabela específica"""
    try:
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default,
                   character_maximum_length, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)

        if not columns:
            return None

        print(f"\n📋 TABELA: {table_name}")
        print("-" * 50)
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            length = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
            precision = f"({col['numeric_precision']},{col['numeric_scale']})" if col['numeric_precision'] else ""

            print(f"   • {col['column_name']}: {col['data_type']}{length}{precision} {nullable}{default}")

        return columns

    except Exception as e:
        print(f"❌ Erro ao inspecionar tabela {table_name}: {e}")
        return None

async def main():
    """Função principal"""
    print("🔍 SIGESCON - INSPEÇÃO DO SCHEMA DO SERVIDOR")
    print("=" * 60)

    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        print("✅ Conexão estabelecida")

        # Lista todas as tabelas
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        print(f"\n📊 INSPECIONANDO {len(tables)} TABELAS:")

        # Inspecciona cada tabela
        for table in tables:
            await inspect_table_schema(conn, table['tablename'])

        print("\n" + "=" * 60)
        print("✅ INSPEÇÃO CONCLUÍDA")

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(main())