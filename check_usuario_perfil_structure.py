#!/usr/bin/env python3
"""
Script para verificar a estrutura da tabela usuario_perfil
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_usuario_perfil_structure():
    """Verificar estrutura da tabela usuario_perfil"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada no .env")
        return

    try:
        conn = await asyncpg.connect(database_url)
        
        print("🔍 VERIFICANDO ESTRUTURA DA TABELA USUARIO_PERFIL")
        print("=" * 60)
        
        # 1. Verificar se a tabela existe
        tabela_existe = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'usuario_perfil'
            );
        """)
        
        if not tabela_existe:
            print("   ❌ Tabela 'usuario_perfil' não existe!")
            return
        
        print("   ✅ Tabela 'usuario_perfil' existe")
        
        # 2. Verificar estrutura da tabela
        print("\n📋 ESTRUTURA DA TABELA USUARIO_PERFIL:")
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
        
        # 3. Verificar se tem a coluna observacoes
        tem_observacoes = any(col['column_name'] == 'observacoes' for col in colunas)
        
        print(f"\n🔍 COLUNA 'observacoes': {'✅ Existe' if tem_observacoes else '❌ Não existe'}")
        
        # 4. Contar registros
        total_registros = await conn.fetchval("SELECT COUNT(*) FROM usuario_perfil")
        registros_ativos = await conn.fetchval("SELECT COUNT(*) FROM usuario_perfil WHERE ativo = TRUE")
        
        print(f"\n📊 DADOS:")
        print(f"   • Total de registros: {total_registros}")
        print(f"   • Registros ativos: {registros_ativos}")
        
        # 5. Mostrar alguns registros
        if total_registros > 0:
            print("\n📄 REGISTROS EXISTENTES:")
            registros = await conn.fetch("""
                SELECT up.*, p.nome as perfil_nome
                FROM usuario_perfil up
                JOIN perfil p ON up.perfil_id = p.id
                ORDER BY up.id
                LIMIT 5
            """)
            
            for reg in registros:
                status = "✅ Ativo" if reg['ativo'] else "❌ Inativo"
                print(f"   • ID {reg['id']}: Usuário {reg['usuario_id']} -> {reg['perfil_nome']} - {status}")
        
        print("\n" + "=" * 60)
        
        # 6. Diagnóstico e solução
        print("\n💡 DIAGNÓSTICO E SOLUÇÃO:")
        if not tem_observacoes:
            print("   🔧 PROBLEMA: Coluna 'observacoes' não existe na tabela usuario_perfil")
            print("   📝 SOLUÇÕES POSSÍVEIS:")
            print("      1. Remover referências à coluna 'observacoes' do código")
            print("      2. Adicionar a coluna 'observacoes' à tabela (se necessária)")
            print("\n   🛠️  COMANDO SQL para adicionar a coluna (se necessário):")
            print("      ALTER TABLE usuario_perfil ADD COLUMN observacoes TEXT;")
        else:
            print("   ✅ Estrutura está correta")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_usuario_perfil_structure())
