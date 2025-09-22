#!/usr/bin/env python3
"""
Script para verificar contratos existentes no banco
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_contratos():
    """Verificar contratos existentes"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada no .env")
        return

    try:
        conn = await asyncpg.connect(database_url)
        
        print("🔍 VERIFICANDO CONTRATOS EXISTENTES")
        print("=" * 50)
        
        # 1. Contar contratos
        total_contratos = await conn.fetchval("SELECT COUNT(*) FROM contrato")
        contratos_ativos = await conn.fetchval("SELECT COUNT(*) FROM contrato WHERE ativo = TRUE")
        
        print(f"   • Total de contratos: {total_contratos}")
        print(f"   • Contratos ativos: {contratos_ativos}")
        
        # 2. Mostrar contratos existentes
        if total_contratos > 0:
            print("\n📋 CONTRATOS EXISTENTES:")
            contratos = await conn.fetch("""
                SELECT id, nr_contrato, objeto, ativo
                FROM contrato
                ORDER BY id
                LIMIT 10
            """)
            
            for contrato in contratos:
                status = "✅ Ativo" if contrato['ativo'] else "❌ Inativo"
                print(f"   • ID {contrato['id']}: Nr {contrato['nr_contrato']} - {contrato['objeto'][:50]}... - {status}")
        
        # 3. Verificar números duplicados
        print("\n🔍 VERIFICANDO NÚMEROS DUPLICADOS:")
        duplicados = await conn.fetch("""
            SELECT nr_contrato, COUNT(*) as total
            FROM contrato 
            WHERE ativo = TRUE
            GROUP BY nr_contrato
            HAVING COUNT(*) > 1
        """)
        
        if duplicados:
            print("   ❌ NÚMEROS DUPLICADOS ENCONTRADOS:")
            for dup in duplicados:
                print(f"      • Nr {dup['nr_contrato']}: {dup['total']} contratos")
        else:
            print("   ✅ Nenhum número duplicado encontrado")
        
        # 4. Próximo número disponível
        print("\n🔢 PRÓXIMO NÚMERO DISPONÍVEL:")
        proximo_numero = await conn.fetchval("""
            SELECT COALESCE(MAX(CAST(nr_contrato AS INTEGER)), 0) + 1
            FROM contrato 
            WHERE ativo = TRUE 
            AND nr_contrato ~ '^[0-9]+$'
        """)
        print(f"   • Sugestão: {proximo_numero}")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_contratos())
