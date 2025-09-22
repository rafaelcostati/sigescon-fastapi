#!/usr/bin/env python3
"""
Script para testar a criação de usuários após as correções
"""
import asyncio
import aiohttp
import json

async def test_create_user():
    """Testar a criação de usuários"""
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # Dados de login (admin)
    login_data = {
        "username": "admin@sigescon.pge.pa.gov.br",
        "password": "admin123"
    }
    
    # Dados do novo usuário
    user_data = {
        "nome": "Teste Usuario",
        "email": "teste@sigescon.gov.br",
        "senha": "123456",
        "cpf": "12345678901",
        "matricula": "TEST001"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🔐 FAZENDO LOGIN...")
            
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
            
            # 2. Testar criação de usuário
            print("\n👤 TESTANDO CRIAÇÃO DE USUÁRIO...")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with session.post(f"{base_url}/usuarios", 
                                  json=user_data, 
                                  headers=headers) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 201:
                    user_result = await response.json()
                    print("✅ Usuário criado com sucesso!")
                    print(f"   ID: {user_result.get('id')}")
                    print(f"   Nome: {user_result.get('nome')}")
                    print(f"   Email: {user_result.get('email')}")
                    
                    # 3. Testar concessão de perfil
                    user_id = user_result.get('id')
                    if user_id:
                        print(f"\n🎭 CONCEDENDO PERFIL FISCAL AO USUÁRIO {user_id}...")
                        
                        perfil_data = {
                            "perfil_ids": [3]  # ID do perfil Fiscal
                        }
                        
                        async with session.post(f"{base_url}/usuarios/{user_id}/perfis/conceder",
                                              json=perfil_data,
                                              headers=headers) as perfil_response:
                            print(f"   Status: {perfil_response.status}")
                            
                            if perfil_response.status == 200:
                                perfil_result = await perfil_response.json()
                                print("✅ Perfil concedido com sucesso!")
                                print(f"   Perfis: {[p.get('perfil_nome') for p in perfil_result]}")
                            else:
                                error_text = await perfil_response.text()
                                print(f"❌ Erro ao conceder perfil: {error_text}")
                    
                else:
                    print(f"❌ Erro na criação do usuário: {response.status}")
                    error_text = await response.text()
                    print(f"   Resposta: {error_text}")
                    
        except Exception as e:
            print(f"❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    print("🧪 TESTANDO CRIAÇÃO DE USUÁRIO")
    print("=" * 50)
    asyncio.run(test_create_user())
