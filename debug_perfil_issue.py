#!/usr/bin/env python3
"""
Script para debugar problema de perfil incorreto sendo exibido
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def debug_perfil_issue():
    """Debugar problema de perfil"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada no .env")
        return

    conn = await asyncpg.connect(database_url)

    try:
        print("🔍 INVESTIGANDO PROBLEMA DE PERFIL")
        print("=" * 50)
        
        # 1. Verificar usuários e seus perfis
        print("\n1️⃣ USUÁRIOS E PERFIS:")
        usuarios = await conn.fetch("""
            SELECT 
                u.id,
                u.nome,
                u.email,
                u.perfil_id as perfil_principal_id,
                p_principal.nome as perfil_principal_nome
            FROM usuario u
            LEFT JOIN perfil p_principal ON u.perfil_id = p_principal.id
            WHERE u.ativo = TRUE
            ORDER BY u.id
        """)
        
        for user in usuarios:
            print(f"   👤 {user['nome']} ({user['email']})")
            print(f"      ID: {user['id']}")
            print(f"      Perfil Principal: {user['perfil_principal_nome']} (ID: {user['perfil_principal_id']})")
            
            # Verificar perfis disponíveis via usuario_perfil
            perfis_disponiveis = await conn.fetch("""
                SELECT p.id, p.nome
                FROM usuario_perfil up
                JOIN perfil p ON up.perfil_id = p.id
                WHERE up.usuario_id = $1 AND up.ativo = TRUE AND p.ativo = TRUE
                ORDER BY p.id
            """, user['id'])
            
            perfis_formatados = [f"{p['nome']} (ID: {p['id']})" for p in perfis_disponiveis]
            print(f"      Perfis Disponíveis: {perfis_formatados}")
            print()
        
        # 2. Verificar contextos de sessão ativos
        print("\n2️⃣ CONTEXTOS DE SESSÃO ATIVOS:")
        contextos = await conn.fetch("""
            SELECT 
                sc.id,
                sc.usuario_id,
                u.nome as usuario_nome,
                sc.perfil_ativo_id,
                p.nome as perfil_ativo_nome,
                sc.sessao_id,
                sc.data_criacao
            FROM session_context sc
            JOIN usuario u ON sc.usuario_id = u.id
            JOIN perfil p ON sc.perfil_ativo_id = p.id
            WHERE sc.ativo = TRUE
            ORDER BY sc.data_criacao DESC
        """)
        
        if contextos:
            for ctx in contextos:
                print(f"   🔑 Sessão ID: {ctx['sessao_id'][:20]}...")
                print(f"      Usuário: {ctx['usuario_nome']} (ID: {ctx['usuario_id']})")
                print(f"      Perfil Ativo: {ctx['perfil_ativo_nome']} (ID: {ctx['perfil_ativo_id']})")
                print(f"      Criado em: {ctx['data_criacao']}")
                print()
        else:
            print("   ⚠️  Nenhum contexto de sessão ativo encontrado")
        
        # 3. Verificar se há inconsistências
        print("\n3️⃣ VERIFICANDO INCONSISTÊNCIAS:")
        
        # Verificar usuários com perfil principal que não está em usuario_perfil
        inconsistencias = await conn.fetch("""
            SELECT 
                u.id,
                u.nome,
                u.perfil_id,
                p.nome as perfil_nome
            FROM usuario u
            JOIN perfil p ON u.perfil_id = p.id
            WHERE u.ativo = TRUE 
            AND NOT EXISTS (
                SELECT 1 FROM usuario_perfil up 
                WHERE up.usuario_id = u.id 
                AND up.perfil_id = u.perfil_id 
                AND up.ativo = TRUE
            )
        """)
        
        if inconsistencias:
            print("   ❌ INCONSISTÊNCIAS ENCONTRADAS:")
            for inc in inconsistencias:
                print(f"      • {inc['nome']}: Perfil principal {inc['perfil_nome']} não está em usuario_perfil")
        else:
            print("   ✅ Nenhuma inconsistência encontrada")
        
        # 4. Verificar duplicatas na tabela usuario_perfil
        print("\n4️⃣ VERIFICANDO DUPLICATAS:")
        duplicatas = await conn.fetch("""
            SELECT usuario_id, perfil_id, COUNT(*) as count
            FROM usuario_perfil 
            WHERE ativo = TRUE
            GROUP BY usuario_id, perfil_id
            HAVING COUNT(*) > 1
        """)
        
        if duplicatas:
            print("   ❌ DUPLICATAS ENCONTRADAS:")
            for dup in duplicatas:
                print(f"      • Usuário {dup['usuario_id']}, Perfil {dup['perfil_id']}: {dup['count']} registros")
        else:
            print("   ✅ Nenhuma duplicata encontrada")
        
        # 5. Sugestões de correção
        print("\n5️⃣ SUGESTÕES DE CORREÇÃO:")
        
        if inconsistencias:
            print("   🔧 Para corrigir inconsistências:")
            print("      1. Execute o comando para sincronizar perfis:")
            print("         UPDATE usuario SET perfil_id = (")
            print("           SELECT perfil_id FROM usuario_perfil")  
            print("           WHERE usuario_id = usuario.id AND ativo = TRUE")
            print("           ORDER BY data_concessao DESC LIMIT 1")
            print("         );")
            print()
            print("      2. Ou adicione os perfis principais em usuario_perfil:")
            for inc in inconsistencias:
                print(f"         INSERT INTO usuario_perfil (usuario_id, perfil_id, ativo, data_concessao)")
                print(f"         VALUES ({inc['id']}, {inc['perfil_id']}, TRUE, NOW());")
        
        print("\n6️⃣ COMANDOS PARA LIMPEZA (se necessário):")
        print("   🧹 Limpar contextos de sessão antigos:")
        print("      DELETE FROM session_context WHERE data_criacao < NOW() - INTERVAL '1 day';")
        print()
        print("   🔄 Forçar novo login (limpar todas as sessões):")
        print("      DELETE FROM session_context;")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_perfil_issue())
