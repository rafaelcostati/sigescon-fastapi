#!/usr/bin/env python3
"""
Script para verificar constraints da tabela usuario_perfil
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_constraints():
    """Verificar constraints da tabela usuario_perfil"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada no .env")
        return

    try:
        conn = await asyncpg.connect(database_url)
        
        print("🔍 VERIFICANDO CONSTRAINTS DA TABELA USUARIO_PERFIL")
        print("=" * 60)
        
        # 1. Verificar estrutura da tabela
        print("\n📋 ESTRUTURA DA TABELA:")
        colunas = await conn.fetch("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'usuario_perfil'
            ORDER BY ordinal_position;
        """)
        
        for coluna in colunas:
            print(f"   • {coluna['column_name']}: {coluna['data_type']} "
                  f"({'NULL' if coluna['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # 2. Verificar constraints/índices únicos
        print("\n🔑 CONSTRAINTS E ÍNDICES:")
        constraints = await conn.fetch("""
            SELECT 
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                tc.is_deferrable,
                tc.initially_deferred
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = 'public'
            AND tc.table_name = 'usuario_perfil'
            ORDER BY tc.constraint_name;
        """)
        
        if constraints:
            for constraint in constraints:
                print(f"   • {constraint['constraint_name']}: {constraint['constraint_type']} "
                      f"({constraint['column_name']})")
        else:
            print("   ❌ Nenhuma constraint encontrada")
        
        # 3. Verificar índices únicos
        print("\n📊 ÍNDICES ÚNICOS:")
        indices = await conn.fetch("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'usuario_perfil'
            AND indexdef LIKE '%UNIQUE%';
        """)
        
        if indices:
            for index in indices:
                print(f"   • {index['indexname']}")
                print(f"     {index['indexdef']}")
        else:
            print("   ❌ Nenhum índice único encontrado")
        
        # 4. Verificar se existe constraint única em (usuario_id, perfil_id)
        print("\n🎯 VERIFICANDO CONSTRAINT ESPECÍFICA (usuario_id, perfil_id):")
        unique_constraint = await conn.fetchval("""
            SELECT constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu1 
                ON tc.constraint_name = ccu1.constraint_name
            JOIN information_schema.constraint_column_usage ccu2 
                ON tc.constraint_name = ccu2.constraint_name
            WHERE tc.table_schema = 'public'
            AND tc.table_name = 'usuario_perfil'
            AND tc.constraint_type = 'UNIQUE'
            AND ccu1.column_name = 'usuario_id'
            AND ccu2.column_name = 'perfil_id';
        """)
        
        if unique_constraint:
            print(f"   ✅ Constraint única encontrada: {unique_constraint}")
        else:
            print("   ❌ Constraint única (usuario_id, perfil_id) NÃO encontrada")
            print("\n💡 SOLUÇÃO:")
            print("   Para corrigir o problema, execute:")
            print("   ALTER TABLE usuario_perfil ADD CONSTRAINT uk_usuario_perfil UNIQUE (usuario_id, perfil_id);")
        
        # 5. Mostrar dados existentes
        print("\n📄 DADOS EXISTENTES:")
        registros = await conn.fetch("""
            SELECT up.*, u.nome as usuario_nome, p.nome as perfil_nome
            FROM usuario_perfil up
            JOIN usuario u ON up.usuario_id = u.id
            JOIN perfil p ON up.perfil_id = p.id
            ORDER BY up.usuario_id, up.perfil_id
            LIMIT 10
        """)
        
        if registros:
            for reg in registros:
                status = "✅" if reg['ativo'] else "❌"
                print(f"   {status} {reg['usuario_nome']} → {reg['perfil_nome']}")
        else:
            print("   📭 Nenhum registro encontrado")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_constraints())
