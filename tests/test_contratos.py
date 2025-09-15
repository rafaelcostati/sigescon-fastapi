# tests/test_contratos.py
import pytest
from httpx import AsyncClient
from typing import Dict, Any
import os
from dotenv import load_dotenv
import uuid
import random
from datetime import date

load_dotenv()

# Fixture de autenticação
@pytest.fixture
def admin_credentials() -> Dict:
    return {"username": os.getenv("ADMIN_EMAIL"), "password": os.getenv("ADMIN_PASSWORD")}

@pytest.fixture
async def admin_headers(async_client: AsyncClient, admin_credentials: Dict) -> Dict:
    response = await async_client.post("/auth/login", data=admin_credentials)
    assert response.status_code == 200, "Falha ao fazer login como admin para obter o token."
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Fixture para criar pré-requisitos (atores do contrato)
@pytest.fixture
async def contract_prerequisites(async_client: AsyncClient, admin_headers: Dict) -> Dict[str, Any]:
    """Cria um gestor, fiscal, contratado, modalidade e status para usar nos testes de contrato."""
    
    async def create_user(perfil_id: int, role: str):
        user_data = {
            "nome": f"{role} Teste Contrato {uuid.uuid4().hex[:6]}",
            "email": f"{role}.contrato.{uuid.uuid4().hex[:6]}@teste.com",
            "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
            "senha": "password123", "perfil_id": perfil_id
        }
        response = await async_client.post("/usuarios/", json=user_data, headers=admin_headers)
        assert response.status_code == 201
        return response.json()

    async def create_contratado():
        contratado_data = {
            "nome": f"Empresa Teste Contrato {uuid.uuid4().hex[:6]}",
            "email": f"empresa.contrato.{uuid.uuid4().hex[:6]}@teste.com",
            "cnpj": f"{random.randint(10**13, 10**14-1)}"
        }
        response = await async_client.post("/contratados/", json=contratado_data, headers=admin_headers)
        assert response.status_code == 201
        return response.json()

    modalidades_resp = await async_client.get("/modalidades/", headers=admin_headers)
    status_list_resp = await async_client.get("/status/", headers=admin_headers)
    perfis_resp = await async_client.get("/perfis/", headers=admin_headers)
    
    assert modalidades_resp.status_code == 200
    assert status_list_resp.status_code == 200
    assert perfis_resp.status_code == 200

    perfis = perfis_resp.json()
    gestor_perfil_id = next(p for p in perfis if p['nome'] == 'Gestor')['id']
    fiscal_perfil_id = next(p for p in perfis if p['nome'] == 'Fiscal')['id']

    gestor = await create_user(gestor_perfil_id, "gestor")
    fiscal = await create_user(fiscal_perfil_id, "fiscal")
    contratado = await create_contratado()
    
    return {
        "gestor_id": gestor["id"],
        "fiscal_id": fiscal["id"],
        "contratado_id": contratado["id"],
        "modalidade_id": modalidades_resp.json()[0]["id"],
        "status_id": next(s for s in status_list_resp.json() if s['nome'] == 'Vigente')['id']
    }

# --- Suite de Testes para Contratos ---

@pytest.mark.asyncio
async def test_crud_contrato_workflow_with_file(async_client: AsyncClient, admin_headers: Dict, contract_prerequisites: Dict):
    """Testa o fluxo completo de CRUD para Contratos, incluindo o upload de ficheiro."""
    
    # --- 1. CREATE COM UPLOAD DE FICHEIRO ---
    form_data = {
        "nr_contrato": f"UPL-{uuid.uuid4().hex[:8]}",
        "objeto": "Contrato de teste com upload de ficheiro.",
        "data_inicio": str(date(2025, 1, 1)),
        "data_fim": str(date(2025, 12, 31)),
        **contract_prerequisites
    }
    
    # Prepara o ficheiro para o upload
    file_content = "Conteúdo do ficheiro de teste."
    files = {"documento_contrato": ("documento_teste.txt", file_content, "text/plain")}

    create_response = await async_client.post("/contratos/", data=form_data, files=files, headers=admin_headers)
    assert create_response.status_code == 201
    created_contrato = create_response.json()
    assert created_contrato["nr_contrato"] == form_data["nr_contrato"]
    # Verifica se o nome do ficheiro foi associado ao contrato
    assert created_contrato["documento_nome_arquivo"] == "documento_teste.txt"
    contrato_id = created_contrato["id"]

    # --- 2. READ BY ID ---
    get_one_response = await async_client.get(f"/contratos/{contrato_id}", headers=admin_headers)
    assert get_one_response.status_code == 200
    fetched_contrato = get_one_response.json()
    assert fetched_contrato["id"] == contrato_id
    assert fetched_contrato["gestor_id"] == contract_prerequisites["gestor_id"]

    # --- 3. READ ALL (com filtro) ---
    get_all_response = await async_client.get(f"/contratos/?nr_contrato={form_data['nr_contrato']}", headers=admin_headers)
    assert get_all_response.status_code == 200
    paginated_data = get_all_response.json()
    assert paginated_data["total_items"] == 1
    assert paginated_data["data"][0]["id"] == contrato_id

    # --- 4. UPDATE ---
    update_data = {"objeto": "Este é um objeto de contrato atualizado após o upload."}
    update_response = await async_client.patch(f"/contratos/{contrato_id}", json=update_data, headers=admin_headers)
    assert update_response.status_code == 200
    assert update_response.json()["objeto"] == update_data["objeto"]

    # --- 5. DELETE ---
    delete_response = await async_client.delete(f"/contratos/{contrato_id}", headers=admin_headers)
    assert delete_response.status_code == 204

    # --- 6. VERIFY DELETE ---
    verify_delete_response = await async_client.get(f"/contratos/{contrato_id}", headers=admin_headers)
    assert verify_delete_response.status_code == 404