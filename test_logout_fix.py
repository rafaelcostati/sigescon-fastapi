#!/usr/bin/env python3
"""
Teste rápido para verificar se o endpoint de logout melhorado funciona
"""
import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"

async def test_logout_endpoints():
    """Testa os novos endpoints de logout"""
    async with httpx.AsyncClient() as client:
        print("🧪 Testando endpoints de logout...")

        # Teste 1: Logout sem token (deve usar logout-anon automaticamente)
        print("\n1. Testando logout anônimo...")
        try:
            response = await client.post(f"{BASE_URL}/auth/logout-anon")
            print(f"   Status: {response.status_code}")
            print(f"   Resposta: {response.json()}")
        except Exception as e:
            print(f"   Erro: {e}")

        # Teste 2: Logout com token inválido (deve ser gracioso)
        print("\n2. Testando logout com token inválido...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/logout",
                headers={"Authorization": "Bearer token_invalido_teste"}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Resposta: {response.json()}")
        except Exception as e:
            print(f"   Erro: {e}")

        print("\n✅ Testes de logout concluídos!")

if __name__ == "__main__":
    asyncio.run(test_logout_endpoints())