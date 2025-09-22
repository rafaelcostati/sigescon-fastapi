#!/usr/bin/env python3
"""
Script para testar a API de usuários após as correções
"""
import asyncio
import aiohttp
import json

async def test_usuarios_api():
    """Testar a API de usuários"""
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # Dados de login (admin)
    login_data = {
        "username": "admin@sigescon.pge.pa.gov.br",
        "password": "admin123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🔐 TESTANDO LOGIN...")
            
            # 1. Fazer login
            async with session.post(f"{base_url}/auth/login", data=login_data) as response:
                if response.status != 200:
                    print(f"❌ Erro no login: {response.status}")
                    text = await response.text()
                    print(f"   Resposta: {text}")
                    return
                
                login_result = await response.json()
                token = login_result.get("access_token")
                
                if not token:
                    print("❌ Token não encontrado na resposta do login")
                    return
                
                print("✅ Login realizado com sucesso")
            
            # 2. Testar endpoint de usuários
            print("\n👥 TESTANDO ENDPOINT DE USUÁRIOS...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            async with session.get(f"{base_url}/usuarios/?page=1&per_page=10", headers=headers) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    usuarios_data = await response.json()
                    print("✅ Endpoint de usuários funcionando!")
                    print(f"   Total de usuários: {usuarios_data.get('total', 'N/A')}")
                    print(f"   Usuários na página: {len(usuarios_data.get('items', []))}")
                    
                    # Mostrar primeiro usuário
                    if usuarios_data.get('items'):
                        primeiro_usuario = usuarios_data['items'][0]
                        print(f"   Primeiro usuário: {primeiro_usuario.get('nome')} ({primeiro_usuario.get('email')})")
                    
                else:
                    print(f"❌ Erro no endpoint de usuários: {response.status}")
                    error_text = await response.text()
                    print(f"   Resposta: {error_text}")
            
            # 3. Testar endpoint de perfis do usuário
            print("\n🎭 TESTANDO PERFIS DO USUÁRIO...")
            
            async with session.get(f"{base_url}/usuarios/1/perfis", headers=headers) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    perfis_data = await response.json()
                    print("✅ Endpoint de perfis funcionando!")
                    print(f"   Perfis do usuário: {[p.get('perfil_nome') for p in perfis_data]}")
                else:
                    print(f"❌ Erro no endpoint de perfis: {response.status}")
                    error_text = await response.text()
                    print(f"   Resposta: {error_text}")
                    
        except Exception as e:
            print(f"❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    print("🧪 TESTANDO API DE USUÁRIOS")
    print("=" * 50)
    asyncio.run(test_usuarios_api())
