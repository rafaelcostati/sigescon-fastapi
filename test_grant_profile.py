#!/usr/bin/env python3
"""
Script para testar a concessão de perfis após as correções
"""
import asyncio
import aiohttp
import json

async def test_grant_profile():
    """Testar a concessão de perfis"""
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # Dados de login (admin)
    login_data = {
        "username": "admin@sigescon.pge.pa.gov.br",
        "password": "admin123"
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
            
            # 2. Listar usuários para pegar um ID
            print("\n👥 BUSCANDO USUÁRIOS...")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with session.get(f"{base_url}/usuarios/?page=1&per_page=5", headers=headers) as response:
                if response.status != 200:
                    print(f"❌ Erro ao buscar usuários: {response.status}")
                    return
                
                usuarios_data = await response.json()
                usuarios = usuarios_data.get('items', [])
                
                if not usuarios:
                    print("❌ Nenhum usuário encontrado")
                    return
                
                # Pegar um usuário que não seja admin (ID 1)
                usuario_teste = None
                for user in usuarios:
                    if user['id'] != 1:  # Não é admin
                        usuario_teste = user
                        break
                
                if not usuario_teste:
                    print("❌ Nenhum usuário não-admin encontrado")
                    return
                
                print(f"✅ Usuário encontrado: {usuario_teste['nome']} (ID: {usuario_teste['id']})")
            
            # 3. Listar perfis disponíveis
            print("\n🎭 BUSCANDO PERFIS...")
            
            async with session.get(f"{base_url}/perfis", headers=headers) as response:
                if response.status != 200:
                    print(f"❌ Erro ao buscar perfis: {response.status}")
                    return
                
                perfis = await response.json()
                print(f"✅ Perfis disponíveis:")
                for perfil in perfis:
                    print(f"   • {perfil['nome']} (ID: {perfil['id']})")
                
                # Pegar IDs dos perfis Fiscal e Gestor
                perfil_fiscal = next((p for p in perfis if p['nome'] == 'Fiscal'), None)
                perfil_gestor = next((p for p in perfis if p['nome'] == 'Gestor'), None)
                
                if not perfil_fiscal:
                    print("❌ Perfil 'Fiscal' não encontrado")
                    return
            
            # 4. Testar concessão de perfil
            user_id = usuario_teste['id']
            print(f"\n🎯 CONCEDENDO PERFIL FISCAL AO USUÁRIO {user_id}...")
            
            perfil_data = {
                "perfil_ids": [perfil_fiscal['id']]
            }
            
            async with session.post(f"{base_url}/usuarios/{user_id}/perfis/conceder",
                                  json=perfil_data,
                                  headers=headers) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    perfil_result = await response.json()
                    print("✅ Perfil concedido com sucesso!")
                    print(f"   Perfis concedidos: {[p.get('perfil_nome') for p in perfil_result]}")
                    
                    # 5. Verificar perfis do usuário
                    print(f"\n🔍 VERIFICANDO PERFIS DO USUÁRIO {user_id}...")
                    
                    async with session.get(f"{base_url}/usuarios/{user_id}/perfis", headers=headers) as perfis_response:
                        if perfis_response.status == 200:
                            user_perfis = await perfis_response.json()
                            print("✅ Perfis do usuário:")
                            for perfil in user_perfis:
                                status = "✅" if perfil.get('ativo') else "❌"
                                print(f"   {status} {perfil.get('perfil_nome')}")
                        else:
                            print(f"❌ Erro ao verificar perfis: {perfis_response.status}")
                    
                    # 6. Testar concessão de múltiplos perfis
                    if perfil_gestor:
                        print(f"\n🎯 CONCEDENDO MÚLTIPLOS PERFIS AO USUÁRIO {user_id}...")
                        
                        multiplos_perfis = {
                            "perfil_ids": [perfil_fiscal['id'], perfil_gestor['id']]
                        }
                        
                        async with session.post(f"{base_url}/usuarios/{user_id}/perfis/conceder",
                                              json=multiplos_perfis,
                                              headers=headers) as multi_response:
                            print(f"   Status: {multi_response.status}")
                            
                            if multi_response.status == 200:
                                multi_result = await multi_response.json()
                                print("✅ Múltiplos perfis concedidos!")
                                print(f"   Perfis: {[p.get('perfil_nome') for p in multi_result]}")
                            else:
                                error_text = await multi_response.text()
                                print(f"❌ Erro ao conceder múltiplos perfis: {error_text}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Erro ao conceder perfil: {error_text}")
                    
        except Exception as e:
            print(f"❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    print("🧪 TESTANDO CONCESSÃO DE PERFIS")
    print("=" * 50)
    asyncio.run(test_grant_profile())
