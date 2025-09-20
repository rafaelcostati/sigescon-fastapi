#!/usr/bin/env python3
"""
Script para diagnosticar diferenças entre banco local e servidor
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings

async def check_database_permissions(conn):
    """Verifica permissões do usuário atual"""
    print("\n🔍 VERIFICANDO PERMISSÕES DO USUÁRIO")
    print("=" * 50)

    try:
        # Verifica usuário atual
        user_info = await conn.fetchrow("SELECT current_user, session_user, current_database()")
        print(f"✅ Usuário atual: {user_info['current_user']}")
        print(f"✅ Usuário da sessão: {user_info['session_user']}")
        print(f"✅ Banco de dados: {user_info['current_database']}")

        # Verifica se é superusuário
        is_superuser = await conn.fetchval("SELECT usesuper FROM pg_user WHERE usename = current_user")
        print(f"🔐 É superusuário: {'✅ SIM' if is_superuser else '❌ NÃO'}")

        # Verifica permissões específicas
        try:
            await conn.execute("SET session_replication_role = 'replica'")
            await conn.execute("SET session_replication_role = 'origin'")
            print("✅ Pode usar session_replication_role")
        except Exception as e:
            print(f"❌ Não pode usar session_replication_role: {e}")

        # Verifica permissões em tabelas
        tables_check = await conn.fetch("""
            SELECT schemaname, tablename,
                   has_table_privilege(current_user, schemaname||'.'||tablename, 'SELECT') as can_select,
                   has_table_privilege(current_user, schemaname||'.'||tablename, 'INSERT') as can_insert,
                   has_table_privilege(current_user, schemaname||'.'||tablename, 'UPDATE') as can_update,
                   has_table_privilege(current_user, schemaname||'.'||tablename, 'DELETE') as can_delete,
                   has_table_privilege(current_user, schemaname||'.'||tablename, 'TRUNCATE') as can_truncate
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        print(f"\n📋 PERMISSÕES EM TABELAS ({len(tables_check)} encontradas):")
        for table in tables_check:
            truncate_status = "✅" if table['can_truncate'] else "❌"
            print(f"   {truncate_status} {table['tablename']} - TRUNCATE: {'SIM' if table['can_truncate'] else 'NÃO'}")

    except Exception as e:
        print(f"❌ Erro ao verificar permissões: {e}")

async def check_database_structure(conn):
    """Verifica estrutura do banco"""
    print("\n🏗️  VERIFICANDO ESTRUTURA DO BANCO")
    print("=" * 50)

    try:
        # Lista todas as tabelas
        tables = await conn.fetch("""
            SELECT tablename, schemaname
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        print(f"📊 Total de tabelas encontradas: {len(tables)}")
        for table in tables:
            print(f"   • {table['tablename']}")

        # Verifica tabelas específicas do SIGESCON
        expected_tables = [
            'usuarios', 'perfil', 'usuario_perfil', 'contratos', 'contratados',
            'pendencias', 'relatorios', 'status', 'status_relatorio', 'status_pendencia',
            'modalidade', 'arquivos'
        ]

        existing_table_names = [t['tablename'] for t in tables]
        missing_tables = [t for t in expected_tables if t not in existing_table_names]
        extra_tables = [t for t in existing_table_names if t not in expected_tables]

        if missing_tables:
            print(f"\n❌ TABELAS AUSENTES ({len(missing_tables)}):")
            for table in missing_tables:
                print(f"   • {table}")
        else:
            print("\n✅ Todas as tabelas essenciais estão presentes")

        if extra_tables:
            print(f"\n🔍 TABELAS EXTRAS ({len(extra_tables)}):")
            for table in extra_tables:
                print(f"   • {table}")

        # Verifica dados em tabelas essenciais
        essential_data = {}
        for table_name in ['perfil', 'status', 'modalidade', 'usuarios']:
            if table_name in existing_table_names:
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                    essential_data[table_name] = count
                except Exception as e:
                    essential_data[table_name] = f"Erro: {e}"

        print(f"\n📊 DADOS ESSENCIAIS:")
        for table, count in essential_data.items():
            print(f"   • {table}: {count} registros")

    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")

async def check_database_version(conn):
    """Verifica versão do PostgreSQL"""
    print("\n🐘 INFORMAÇÕES DO POSTGRESQL")
    print("=" * 50)

    try:
        version = await conn.fetchval("SELECT version()")
        print(f"✅ Versão: {version}")

        # Configurações importantes
        configs = await conn.fetch("""
            SELECT name, setting, unit, context
            FROM pg_settings
            WHERE name IN ('max_connections', 'shared_buffers', 'effective_cache_size',
                          'maintenance_work_mem', 'checkpoint_completion_target', 'wal_buffers')
        """)

        print("\n⚙️  CONFIGURAÇÕES IMPORTANTES:")
        for config in configs:
            unit = f" {config['unit']}" if config['unit'] else ""
            print(f"   • {config['name']}: {config['setting']}{unit}")

    except Exception as e:
        print(f"❌ Erro ao verificar versão: {e}")

async def main():
    """Função principal de diagnóstico"""
    print("🔧 SIGESCON - DIAGNÓSTICO DO SERVIDOR DE BANCO")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔗 URL do banco: {settings.DATABASE_URL}")
    print("=" * 60)

    try:
        # Conecta ao banco
        conn = await asyncpg.connect(settings.DATABASE_URL)
        print("✅ Conexão com banco de dados estabelecida")

        # Executa diagnósticos
        await check_database_version(conn)
        await check_database_permissions(conn)
        await check_database_structure(conn)

        print("\n" + "=" * 60)
        print("✅ DIAGNÓSTICO CONCLUÍDO")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            await conn.close()
            print("✅ Conexão com banco encerrada")

if __name__ == "__main__":
    asyncio.run(main())