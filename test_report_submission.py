#!/usr/bin/env python3
"""
Teste para verificar se o envio de relatório está funcionando após a correção
"""
import asyncio
import httpx
import json

async def test_report_submission():
    """Teste para envio de relatório fiscal"""

    print("🧪 TESTE DE ENVIO DE RELATÓRIO FISCAL")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # Login com Rafael Fiscal
    login_data = {
        "username": "rafael.costa@pge.pa.gov.br",
        "password": "xpto1661WIN"
    }

    async with httpx.AsyncClient() as client:
        try:
            # 1. Login
            print("\n1. 🔐 Fazendo login...")
            response = await client.post(f"{base_url}/auth/login", data=login_data)
            print(f"   Status do login: {response.status_code}")

            if response.status_code != 200:
                print(f"   ❌ Falha no login: {response.text}")
                return False

            login_result = response.json()
            token = login_result.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Alterar para perfil Fiscal
            print("\n2. 🔄 Alternando para perfil Fiscal...")
            switch_data = {"novo_perfil_id": 3}  # Fiscal profile ID
            response = await client.post(f"{base_url}/auth/alternar-perfil", json=switch_data, headers=headers)
            if response.status_code == 200:
                print("   ✅ Perfil alterado para Fiscal")
                # Atualizar token se necessário
                switch_result = response.json()
                new_token = switch_result.get('access_token')
                if new_token:
                    headers = {"Authorization": f"Bearer {new_token}"}
            else:
                print(f"   ❌ Erro ao alterar perfil: {response.status_code}")

            # 3. Buscar pendências para pegar uma pendencia_id
            print("\n3. 📋 Buscando pendências...")
            response = await client.get(f"{base_url}/api/v1/dashboard/fiscal/completo", headers=headers)
            if response.status_code == 200:
                dashboard_data = response.json()
                pendencias = dashboard_data.get('minhas_pendencias', [])
                print(f"   ✅ Encontradas {len(pendencias)} pendências")

                if not pendencias:
                    print("   ⚠️ Nenhuma pendência encontrada para testar")
                    return True

                # Usar a primeira pendência
                primeira_pendencia = pendencias[0]
                contrato_id = primeira_pendencia['contrato_id']
                pendencia_id = primeira_pendencia['pendencia_id']
                print(f"   📝 Testando com contrato {contrato_id}, pendência {pendencia_id}")
            else:
                print(f"   ❌ Erro ao buscar pendências: {response.status_code}")
                return False

            # 4. Criar arquivo de teste simples
            print("\n4. 📄 Preparando arquivo de teste...")
            test_content = b"Relatorio fiscal de teste - conteudo do arquivo"

            # 5. Submeter relatório
            print("\n5. 📤 Enviando relatório...")

            files = {
                "arquivo": ("relatorio_teste.txt", test_content, "text/plain")
            }
            data = {
                "observacoes_fiscal": "Relatório de teste enviado automaticamente",
                "pendencia_id": pendencia_id
            }

            response = await client.post(
                f"{base_url}/api/v1/contratos/{contrato_id}/relatorios/",
                headers=headers,
                files=files,
                data=data
            )

            print(f"   Status do envio: {response.status_code}")

            if response.status_code == 201:
                print("   ✅ RELATÓRIO ENVIADO COM SUCESSO!")
                result_data = response.json()
                print(f"   📊 ID do relatório: {result_data.get('id')}")
                print(f"   📁 Arquivo: {result_data.get('nome_arquivo', 'N/A')}")
                print(f"   🏷️ Status: {result_data.get('status_relatorio', 'N/A')}")
                return True
            else:
                print(f"   ❌ ERRO no envio: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Erro durante o teste: {e}")
            return False

async def main():
    """Função principal"""
    print("🚀 INICIANDO TESTE DE ENVIO DE RELATÓRIO")

    success = await test_report_submission()

    print("\n" + "=" * 60)
    print("📊 RESULTADO DO TESTE")
    print("=" * 60)

    if success:
        print("✅ TESTE PASSOU! Envio de relatório funcionando.")
    else:
        print("❌ TESTE FALHOU! Problema com envio de relatório.")
        print("🔧 Verificar logs do servidor para mais detalhes.")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)