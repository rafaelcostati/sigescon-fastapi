#!/usr/bin/env python3
"""
Teste das novas funcionalidades de gerenciamento de arquivos de contrato.
Testa listar, baixar e excluir arquivos de um contrato específico.
"""

import requests
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

def authenticate():
    """Autentica e retorna o token"""
    login_data = {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Erro na autenticação: {response.status_code}")
        return None

def test_listar_arquivos_contrato(token, contrato_id):
    """Testa a listagem de arquivos de um contrato"""
    print(f"📂 Testando listagem de arquivos do contrato {contrato_id}...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/contratos/{contrato_id}/arquivos", headers=headers)

    if response.status_code == 200:
        arquivos_data = response.json()
        print(f"✅ Listagem bem-sucedida!")
        print(f"📊 Total de arquivos: {arquivos_data['total_arquivos']}")
        print(f"📄 Contrato ID: {arquivos_data['contrato_id']}")

        if arquivos_data['arquivos']:
            print("📋 Arquivos encontrados:")
            for arquivo in arquivos_data['arquivos']:
                tamanho_kb = arquivo['tamanho_bytes'] / 1024 if arquivo['tamanho_bytes'] else 0
                print(f"  - ID: {arquivo['id']} | {arquivo['nome_arquivo']} ({tamanho_kb:.2f} KB)")

            return arquivos_data['arquivos'][0]['id']  # Retorna o ID do primeiro arquivo para outros testes
        else:
            print("📭 Nenhum arquivo encontrado neste contrato")
            return None
    else:
        print(f"❌ Erro na listagem: {response.status_code}")
        print(f"📝 Resposta: {response.text}")
        return None

def test_download_arquivo(token, contrato_id, arquivo_id):
    """Testa o download de um arquivo específico"""
    print(f"⬇️ Testando download do arquivo {arquivo_id} do contrato {contrato_id}...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/contratos/{contrato_id}/arquivos/{arquivo_id}/download",
        headers=headers
    )

    if response.status_code == 200:
        print(f"✅ Download bem-sucedido!")
        print(f"📄 Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"📊 Tamanho do arquivo: {len(response.content)} bytes")

        # Verifica se tem header de filename
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
            print(f"📁 Nome do arquivo: {filename}")

        return True
    else:
        print(f"❌ Erro no download: {response.status_code}")
        print(f"📝 Resposta: {response.text}")
        return False

def test_excluir_arquivo(token, contrato_id, arquivo_id):
    """Testa a exclusão de um arquivo específico"""
    print(f"🗑️ Testando exclusão do arquivo {arquivo_id} do contrato {contrato_id}...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{BASE_URL}/api/v1/contratos/{contrato_id}/arquivos/{arquivo_id}",
        headers=headers
    )

    if response.status_code == 204:
        print(f"✅ Arquivo excluído com sucesso!")
        return True
    else:
        print(f"❌ Erro na exclusão: {response.status_code}")
        print(f"📝 Resposta: {response.text}")
        return False

def main():
    print("=" * 60)
    print("🧪 TESTE DE GERENCIAMENTO DE ARQUIVOS DE CONTRATO")
    print("=" * 60)

    # 1. Autenticar
    print("🔐 Autenticando...")
    token = authenticate()
    if not token:
        print("💥 Falha na autenticação!")
        return

    print("✅ Autenticação bem-sucedida!")

    # 2. Usar um contrato existente (do teste anterior)
    contrato_id = 101  # ID do contrato criado no teste anterior

    # 3. Testar listagem de arquivos
    primeiro_arquivo_id = test_listar_arquivos_contrato(token, contrato_id)

    if primeiro_arquivo_id:
        # 4. Testar download do primeiro arquivo
        download_success = test_download_arquivo(token, contrato_id, primeiro_arquivo_id)

        if download_success:
            print("\n⚠️ INFORMAÇÃO: Pulando teste de exclusão para preservar os arquivos de teste")
    else:
        print("📭 Nenhum arquivo encontrado para testar download e exclusão")

    print("\n" + "=" * 60)
    print("✅ TESTES DE GERENCIAMENTO DE ARQUIVOS CONCLUÍDOS!")
    print("=" * 60)

if __name__ == "__main__":
    main()