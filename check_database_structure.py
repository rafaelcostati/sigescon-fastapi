#!/usr/bin/env python3
"""
Script para verificar a estrutura atual do banco de dados
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_database_structure():
    """Verificar estrutura do banco"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada no .env")
        return

    try:
        conn = await asyncpg.connect(database_url)
        
        print("🔍 VERIFICANDO ESTRUTURA DO BANCO DE DADOS")
        print("=" * 50)
        
        # 1. Verificar se a tabela usuario existe
        print("\n1️⃣ VERIFICANDO TABELA USUARIO:")
        tabela_existe = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'usuario'
            );
        """)
        
        if not tabela_existe:
            print("   ❌ Tabela 'usuario' não existe!")
            return
        
        print("   ✅ Tabela 'usuario' existe")
        
        # 2. Verificar estrutura da tabela usuario
        print("\n2️⃣ ESTRUTURA DA TABELA USUARIO:")
        colunas = await conn.fetch("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'usuario'
            ORDER BY ordinal_position;
        """)
        
        for coluna in colunas:
            print(f"   • {coluna['column_name']}: {coluna['data_type']} "
                  f"({'NULL' if coluna['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # 3. Verificar se tem campo senha ou senha_hash
        print("\n3️⃣ VERIFICANDO CAMPO DE SENHA:")
        tem_senha = any(col['column_name'] == 'senha' for col in colunas)
        tem_senha_hash = any(col['column_name'] == 'senha_hash' for col in colunas)
        
        if tem_senha:
            print("   🔍 Campo 'senha' encontrado")
        if tem_senha_hash:
            print("   🔍 Campo 'senha_hash' encontrado")
        
        if not tem_senha and not tem_senha_hash:
            print("   ❌ Nenhum campo de senha encontrado!")
        
        # 4. Contar usuários
        print("\n4️⃣ CONTAGEM DE USUÁRIOS:")
        total_usuarios = await conn.fetchval("SELECT COUNT(*) FROM usuario")
        usuarios_ativos = await conn.fetchval("SELECT COUNT(*) FROM usuario WHERE ativo = TRUE")
        
        print(f"   • Total de usuários: {total_usuarios}")
        print(f"   • Usuários ativos: {usuarios_ativos}")
        
        # 5. Se tem usuários, mostrar alguns dados (sem senha)
        if total_usuarios > 0:
            print("\n5️⃣ USUÁRIOS EXISTENTES:")
            usuarios = await conn.fetch("""
                SELECT id, nome, email, ativo
                FROM usuario
                ORDER BY id
                LIMIT 5
            """)
            
            for user in usuarios:
                status = "✅ Ativo" if user['ativo'] else "❌ Inativo"
                print(f"   • ID {user['id']}: {user['nome']} ({user['email']}) - {status}")
        
        # 6. Verificar outras tabelas importantes
        print("\n6️⃣ OUTRAS TABELAS:")
        tabelas = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tabelas_importantes = ['perfil', 'usuario_perfil', 'session_context']
        for tabela_nome in tabelas_importantes:
            existe = any(t['table_name'] == tabela_nome for t in tabelas)
            status = "✅" if existe else "❌"
            print(f"   {status} {tabela_nome}")
        
        print("\n" + "=" * 50)
        
        # 7. Diagnóstico
        print("\n7️⃣ DIAGNÓSTICO:")
        if tem_senha and not tem_senha_hash:
            print("   🔧 PROBLEMA: Banco usa 'senha' mas código espera 'senha_hash'")
            print("   💡 SOLUÇÃO: Renomear coluna ou atualizar código")
        elif tem_senha_hash and not tem_senha:
            print("   ✅ Estrutura correta: usando 'senha_hash'")
        elif tem_senha and tem_senha_hash:
            print("   ⚠️  ATENÇÃO: Ambos os campos existem - pode haver inconsistência")
        
        if total_usuarios == 0:
            print("   ⚠️  Banco vazio - execute o setup para criar usuários")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_database_structure())
