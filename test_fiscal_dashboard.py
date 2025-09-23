#!/usr/bin/env python3
"""
Teste específico para verificar problema de autenticação no dashboard fiscal
"""
import asyncio
import httpx
import json

async def test_fiscal_dashboard():
    """Teste para verificar autenticação fiscal"""

    print("🧪 TESTE DE AUTENTICAÇÃO - DASHBOARD FISCAL")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # 1. Login com usuário que tem perfil Fiscal
    print("\n1. 🔐 Fazendo login...")
    login_data = {
        "username": "rafael.costa@pge.pa.gov.br",
        "password": "xpto1661WIN"
    }

    async with httpx.AsyncClient() as client:
        try:
            # Login
            response = await client.post(f"{base_url}/auth/login", data=login_data)
            print(f"   Status do login: {response.status_code}")

            if response.status_code != 200:
                print(f"   ❌ Falha no login: {response.text}")
                return False

            login_result = response.json()
            token = login_result.get("access_token")
            print(f"   ✅ Login realizado com sucesso")
            print(f"   Token: {token[:50]}...")

            headers = {"Authorization": f"Bearer {token}"}

            # 2. Verificar dados do usuário
            print("\n2. 👤 Verificando dados do usuário...")
            response = await client.get(f"{base_url}/api/v1/usuarios/me", headers=headers)
            print(f"   Status /usuarios/me: {response.status_code}")

            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✅ Usuário: {user_data.get('nome')} (ID: {user_data.get('id')})")
            else:
                print(f"   ❌ Erro ao buscar usuário: {response.text}")

            # 3. Verificar perfis do usuário
            print("\n3. 🎭 Verificando perfis do usuário...")
            user_id = 2  # Rafael Fiscal
            response = await client.get(f"{base_url}/api/v1/usuarios/{user_id}/perfis/completo", headers=headers)
            print(f"   Status /perfis/completo: {response.status_code}")

            if response.status_code == 200:
                perfis_data = response.json()
                print(f"   ✅ Perfis response: {perfis_data}")
                if isinstance(perfis_data, dict) and 'perfis' in perfis_data:
                    print(f"   ✅ Perfis encontrados: {len(perfis_data['perfis'])}")
                    for i, perfil_nome in enumerate(perfis_data['perfis']):
                        perfil_id = perfis_data['perfil_ids'][i] if i < len(perfis_data.get('perfil_ids', [])) else 'N/A'
                        print(f"      - {perfil_nome} (ID: {perfil_id})")
                else:
                    print(f"   ⚠️  Estrutura inesperada: {type(perfis_data)}")
            else:
                print(f"   ❌ Erro ao buscar perfis: {response.text}")

            # 4. Verificar contexto atual
            print("\n4. 🎯 Verificando contexto de sessão...")
            response = await client.get(f"{base_url}/auth/contexto", headers=headers)
            print(f"   Status /auth/contexto: {response.status_code}")

            if response.status_code == 200:
                context_data = response.json()
                print(f"   ✅ Perfil ativo: {context_data.get('perfil_ativo_nome')}")
                print(f"   ✅ Sessão ID: {context_data.get('session_id')}")
            else:
                print(f"   ❌ Erro no contexto: {response.text}")

            # 5. Alterar para perfil Fiscal
            print("\n5. 🔄 Alternando para perfil Fiscal...")
            switch_data = {"novo_perfil_id": 3}  # Fiscal profile ID
            response = await client.post(f"{base_url}/auth/alternar-perfil", json=switch_data, headers=headers)
            print(f"   Status alternar-perfil: {response.status_code}")

            if response.status_code == 200:
                switch_result = response.json()
                print(f"   ✅ Perfil alterado: {switch_result.get('contexto_sessao', {}).get('perfil_ativo_nome')}")

                # Update token if provided
                new_token = switch_result.get('access_token')
                if new_token:
                    headers = {"Authorization": f"Bearer {new_token}"}
                    print(f"   ✅ Token atualizado")
            else:
                print(f"   ❌ Erro ao alterar perfil: {response.text}")

            # 6. Verificar contexto após alternância
            print("\n6. 🎯 Verificando contexto após alternância...")
            response = await client.get(f"{base_url}/auth/contexto", headers=headers)
            print(f"   Status /auth/contexto: {response.status_code}")

            if response.status_code == 200:
                context_data = response.json()
                print(f"   ✅ Perfil ativo atual: {context_data.get('perfil_ativo_nome')}")
            else:
                print(f"   ❌ Erro no contexto: {response.text}")

            # 7. Tentar acessar dashboard fiscal
            print("\n7. 📊 Testando dashboard fiscal...")
            response = await client.get(f"{base_url}/api/v1/dashboard/fiscal/completo", headers=headers)
            print(f"   Status /dashboard/fiscal/completo: {response.status_code}")

            if response.status_code == 200:
                dashboard_data = response.json()
                print(f"   ✅ Dashboard fiscal acessível!")
                print(f"   ✅ Dados: {list(dashboard_data.keys())}")
                return True
            else:
                print(f"   ❌ ERRO no dashboard fiscal: {response.text}")

                # 8. Se der erro, verificar se consegue com outro endpoint fiscal
                print("\n8. 🔄 Testando endpoint alternativo...")
                response = await client.get(f"{base_url}/api/v1/dashboard/fiscal/minhas-pendencias", headers=headers)
                print(f"   Status /dashboard/fiscal/minhas-pendencias: {response.status_code}")

                if response.status_code == 200:
                    print(f"   ✅ Endpoint alternativo funciona")
                else:
                    print(f"   ❌ Endpoint alternativo também falha: {response.text}")

                return False

        except Exception as e:
            print(f"❌ Erro durante os testes: {e}")
            return False

async def main():
    """Função principal"""
    print("🚀 INICIANDO TESTE DE DASHBOARD FISCAL")

    success = await test_fiscal_dashboard()

    print("\n" + "=" * 60)
    print("📊 RESULTADO DO TESTE")
    print("=" * 60)

    if success:
        print("✅ TESTE PASSOU! Dashboard fiscal funcionando.")
    else:
        print("❌ TESTE FALHOU! Problema com dashboard fiscal.")
        print("🔧 Verificar logs do servidor para mais detalhes.")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)