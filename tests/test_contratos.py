# tests/test_contratos.py - VERSÃO CORRIGIDA
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any
import os
from dotenv import load_dotenv
import uuid
import random
from datetime import date

load_dotenv()

# Fixture de autenticação
@pytest_asyncio.fixture
def admin_credentials() -> Dict:
    return {"username": os.getenv("ADMIN_EMAIL"), "password": os.getenv("ADMIN_PASSWORD")}

@pytest_asyncio.fixture
async def admin_headers(async_client: AsyncClient, admin_credentials: Dict) -> Dict:
    response = await async_client.post("/auth/login", data=admin_credentials)
    assert response.status_code == 200, "Falha ao fazer login como admin para obter o token."
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Fixture para criar pré-requisitos (atores do contrato)
@pytest_asyncio.fixture
async def contract_prerequisites(async_client: AsyncClient, admin_headers: Dict) -> Dict[str, Any]:
    """Cria um gestor, fiscal, contratado, modalidade e status para usar nos testes de contrato."""
    
    async def create_user(perfil_id: int, role: str):
        # Cria usuário com perfil Fiscal como padrão (necessário devido à constraint NOT NULL)
        user_data = {
            "nome": f"{role} Teste Contrato {uuid.uuid4().hex[:6]}",
            "email": f"{role.lower()}.contrato.{uuid.uuid4().hex[:6]}@teste.com",
            "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
            "senha": "password123",
            "perfil_id": 3  # Fiscal como padrão temporário
        }
        response = await async_client.post("/api/v1/usuarios/", json=user_data, headers=admin_headers)
        assert response.status_code == 201
        user = response.json()

        # Se o perfil desejado não for Fiscal (3), concede o perfil correto
        if perfil_id != 3:
            perfil_data = {"perfil_ids": [perfil_id]}
            perfil_response = await async_client.post(
                f"/api/v1/usuarios/{user['id']}/perfis/conceder",
                json=perfil_data,
                headers=admin_headers
            )
            assert perfil_response.status_code == 200

        return user

    async def create_contratado():
        contratado_data = {
            "nome": f"Empresa Teste Contrato {uuid.uuid4().hex[:6]}",
            "email": f"empresa.contrato.{uuid.uuid4().hex[:6]}@teste.com",
            "cnpj": f"{random.randint(10**13, 10**14-1)}"
        }
        response = await async_client.post("/api/v1/contratados/", json=contratado_data, headers=admin_headers)
        assert response.status_code == 201
        return response.json()

    # Busca dados auxiliares
    modalidades_resp = await async_client.get("/api/v1/modalidades/", headers=admin_headers)
    status_list_resp = await async_client.get("/api/v1/status/", headers=admin_headers)
    perfis_resp = await async_client.get("/api/v1/perfis/", headers=admin_headers)
    
    assert modalidades_resp.status_code == 200
    assert status_list_resp.status_code == 200
    assert perfis_resp.status_code == 200

    perfis = perfis_resp.json()
    gestor_perfil_id = next(p for p in perfis if p['nome'] == 'Gestor')['id']
    fiscal_perfil_id = next(p for p in perfis if p['nome'] == 'Fiscal')['id']

    # Cria usuários e contratado
    gestor = await create_user(gestor_perfil_id, "Gestor")
    fiscal = await create_user(fiscal_perfil_id, "Fiscal")
    contratado = await create_contratado()
    
    return {
        "gestor_id": gestor["id"],
        "fiscal_id": fiscal["id"],
        "contratado_id": contratado["id"],
        "modalidade_id": modalidades_resp.json()[0]["id"],
        "status_id": next(s for s in status_list_resp.json() if s['nome'] == 'Ativo')['id']
    }

# --- Suite de Testes para Contratos ---

@pytest.mark.asyncio
async def test_crud_contrato_workflow_with_file(async_client: AsyncClient, admin_headers: Dict, contract_prerequisites: Dict):
    """Testa o fluxo completo de CRUD para Contratos, incluindo o upload de arquivo."""
    
    # --- 1. CREATE COM UPLOAD DE ARQUIVO ---
    form_data = {
        "nr_contrato": f"UPL-{uuid.uuid4().hex[:8]}",
        "objeto": "Contrato de teste com upload de arquivo.",
        "data_inicio": str(date(2025, 1, 1)),
        "data_fim": str(date(2025, 12, 31)),
        **contract_prerequisites
    }
    
    # Prepara o arquivo para o upload
    file_content = "Conteúdo do arquivo de teste."
    files = {"documento_contrato": ("documento_teste.txt", file_content, "text/plain")}

    create_response = await async_client.post("/api/v1/contratos/", data=form_data, files=files, headers=admin_headers)
    assert create_response.status_code == 201
    created_contrato = create_response.json()
    assert created_contrato["nr_contrato"] == form_data["nr_contrato"]
    # Verifica se o nome do arquivo foi associado ao contrato
    assert created_contrato["documento_nome_arquivo"] == "documento_teste.txt"
    contrato_id = created_contrato["id"]

    # --- 2. READ BY ID ---
    get_one_response = await async_client.get(f"/api/v1/contratos/{contrato_id}", headers=admin_headers)
    assert get_one_response.status_code == 200
    fetched_contrato = get_one_response.json()
    assert fetched_contrato["id"] == contrato_id
    assert fetched_contrato["gestor_id"] == contract_prerequisites["gestor_id"]

    # --- 3. READ ALL (com filtro) ---
    get_all_response = await async_client.get(f"/api/v1/contratos/?nr_contrato={form_data['nr_contrato']}", headers=admin_headers)
    assert get_all_response.status_code == 200
    paginated_data = get_all_response.json()
    assert paginated_data["total_items"] == 1
    assert paginated_data["data"][0]["id"] == contrato_id

    # --- 4. UPDATE ---
    update_data = {"objeto": "Este é um objeto de contrato atualizado após o upload."}
    update_response = await async_client.patch(f"/api/v1/contratos/{contrato_id}", data=update_data, headers=admin_headers)
    assert update_response.status_code == 200
    assert update_response.json()["objeto"] == update_data["objeto"]

    # --- 5. DELETE ---
    delete_response = await async_client.delete(f"/api/v1/contratos/{contrato_id}", headers=admin_headers)
    assert delete_response.status_code == 204

    # --- 6. VERIFY DELETE ---
    verify_delete_response = await async_client.get(f"/api/v1/contratos/{contrato_id}", headers=admin_headers)
    assert verify_delete_response.status_code == 404

@pytest.mark.asyncio
async def test_contract_permissions(async_client: AsyncClient, admin_headers: Dict, contract_prerequisites: Dict):
    """Testa as permissões de acesso a contratos."""
    
    # 1. Cria um contrato
    form_data = {
        "nr_contrato": f"PERM-{uuid.uuid4().hex[:8]}",
        "objeto": "Contrato para teste de permissões",
        "data_inicio": str(date(2025, 1, 1)),
        "data_fim": str(date(2025, 12, 31)),
        **contract_prerequisites
    }
    
    create_response = await async_client.post("/api/v1/contratos/", data=form_data, headers=admin_headers)
    assert create_response.status_code == 201
    contrato_id = create_response.json()["id"]
    
    # 2. Cria um usuário fiscal que NÃO é fiscal deste contrato
    other_fiscal_data = {
        "nome": f"Outro Fiscal {uuid.uuid4().hex[:6]}",
        "email": f"outro.fiscal.{uuid.uuid4().hex[:6]}@teste.com",
        "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
        "senha": "password123",
        "perfil_id": 3  # Fiscal como padrão temporário
    }

    other_fiscal_resp = await async_client.post("/api/v1/usuarios/", json=other_fiscal_data, headers=admin_headers)
    assert other_fiscal_resp.status_code == 201
    other_fiscal = other_fiscal_resp.json()
    other_fiscal_id = other_fiscal["id"]

    # Conceder perfil fiscal via sistema de múltiplos perfis
    perfil_data = {"perfil_ids": [3]}  # Fiscal
    perfil_response = await async_client.post(
        f"/api/v1/usuarios/{other_fiscal_id}/perfis/conceder",
        json=perfil_data,
        headers=admin_headers
    )
    assert perfil_response.status_code == 200
    
    # 3. Login como o fiscal que NÃO tem acesso ao contrato
    login_resp = await async_client.post("/auth/login", data={"username": other_fiscal_data["email"], "password": other_fiscal_data["senha"]})
    assert login_resp.status_code == 200
    other_fiscal_token = login_resp.json()["access_token"]
    other_fiscal_headers = {"Authorization": f"Bearer {other_fiscal_token}"}
    
    # 4. Fiscal sem permissão NÃO pode ver detalhes do contrato (isolamento de dados)
    get_response = await async_client.get(f"/api/v1/contratos/{contrato_id}", headers=other_fiscal_headers)
    assert get_response.status_code == 404  # Not Found (devido ao isolamento por perfil)
    
    # 5. Admin PODE ver o contrato
    admin_get_response = await async_client.get(f"/api/v1/contratos/{contrato_id}", headers=admin_headers)
    assert admin_get_response.status_code == 200
    
    # 6. Limpa o usuário de teste
    await async_client.delete(f"/api/v1/usuarios/{other_fiscal_id}", headers=admin_headers)

@pytest.mark.asyncio
async def test_unauthorized_contract_access(async_client: AsyncClient):
    """Testa que usuários não autenticados não podem acessar contratos."""
    
    # Tenta listar contratos sem autenticação
    response = await async_client.get("/api/v1/contratos/")
    assert response.status_code == 401
    
    # Tenta criar contrato sem autenticação
    form_data = {
        "nr_contrato": "TEST-001",
        "objeto": "Teste sem auth",
        "data_inicio": str(date(2025, 1, 1)),
        "data_fim": str(date(2025, 12, 31)),
        "contratado_id": 1,
        "modalidade_id": 1,
        "status_id": 1,
        "gestor_id": 1,
        "fiscal_id": 1
    }
    
    create_response = await async_client.post("/api/v1/contratos/", data=form_data)
    assert create_response.status_code == 401