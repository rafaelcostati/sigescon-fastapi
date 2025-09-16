# tests/test_modalidades.py 
import pytest
from httpx import AsyncClient
from typing import Dict
import os
from dotenv import load_dotenv
import uuid
import random

load_dotenv()

@pytest.fixture(scope="module")
def admin_credentials() -> Dict:
    return {"username": os.getenv("ADMIN_EMAIL"), "password": os.getenv("ADMIN_PASSWORD")}

@pytest.fixture
async def admin_token(async_client: AsyncClient, admin_credentials: Dict) -> str:
    response = await async_client.post("/auth/login", data=admin_credentials)
    return response.json()["access_token"]

@pytest.fixture
async def admin_headers(admin_token: str) -> Dict:
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.mark.asyncio
async def test_crud_modalidades_workflow(async_client: AsyncClient, admin_headers: Dict):
    """Testa o fluxo completo de CRUD para Modalidades."""
    
    unique_name = f"Modalidade Teste {uuid.uuid4().hex[:6]}"
    
    # 1. CREATE ()
    print("\n--- Testando CREATE de Modalidade ---")
    create_response = await async_client.post(
        "/api/v1/modalidades/",
        json={"nome": unique_name},
        headers=admin_headers
    )
    assert create_response.status_code == 201
    created_data = create_response.json()
    assert created_data["nome"] == unique_name
    modalidade_id = created_data["id"]
    print(f"✓ Modalidade '{unique_name}' (ID: {modalidade_id}) criada com sucesso.")

    # 2. READ ALL ()
    print("\n--- Testando READ ALL ---")
    get_all_response = await async_client.get("/api/v1/modalidades/", headers=admin_headers)
    assert get_all_response.status_code == 200
    modalidades_list = get_all_response.json()
    assert isinstance(modalidades_list, list)
    assert unique_name in [m["nome"] for m in modalidades_list]
    print("✓ Lista de modalidades lida com sucesso.")

    # 3. UPDATE ()
    print("\n--- Testando UPDATE ---")
    updated_name = f"Modalidade Atualizada {uuid.uuid4().hex[:6]}"
    update_response = await async_client.patch(
        f"/api/v1/modalidades/{modalidade_id}",
        json={"nome": updated_name},
        headers=admin_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["nome"] == updated_name
    print(f"✓ Modalidade ID {modalidade_id} atualizada para '{updated_name}'.")

    # 4. DELETE ()
    print("\n--- Testando DELETE ---")
    delete_response = await async_client.delete(f"/api/v1/modalidades/{modalidade_id}", headers=admin_headers)
    assert delete_response.status_code == 204
    print(f"✓ Modalidade ID {modalidade_id} deletada com sucesso.")

    # 5. VERIFY DELETE ()
    print("\n--- Verificando DELETE ---")
    verify_response = await async_client.get("/api/v1/modalidades/", headers=admin_headers)
    assert updated_name not in [m["nome"] for m in verify_response.json()]
    print("✓ Modalidade deletada não aparece mais na lista.")
    
@pytest.mark.asyncio
async def test_non_admin_cannot_write(async_client: AsyncClient, admin_headers: Dict):
    """Testa se um usuário não-admin (fiscal) não pode criar, atualizar ou deletar."""
    # Criar um usuário fiscal para o teste
    fiscal_data = {
        "nome": f"Fiscal Teste Modalidade {uuid.uuid4().hex[:6]}",
        "email": f"fiscal.modalidade.{uuid.uuid4().hex[:6]}@teste.com",
        "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),  # CPF aleatório
        "senha": "password123",
        "perfil_id": 3
    }

    #  para criar usuário
    create_user_response = await async_client.post("/api/v1/usuarios/", json=fiscal_data, headers=admin_headers)
    assert create_user_response.status_code == 201, f"Falha ao criar usuário fiscal de teste: {create_user_response.text}"

    # Login como fiscal
    login_resp = await async_client.post("/auth/login", data={"username": fiscal_data["email"], "password": fiscal_data["senha"]})
    assert login_resp.status_code == 200, "Falha ao logar com o usuário fiscal de teste."
    fiscal_token = login_resp.json()["access_token"]
    fiscal_headers = {"Authorization": f"Bearer {fiscal_token}"}
    
    # Fiscal TENTA criar (deve falhar) - 
    create_fail = await async_client.post("/api/v1/modalidades/", json={"nome": "Tentativa Fiscal"}, headers=fiscal_headers)
    assert create_fail.status_code == 403
    
    # Fiscal TENTA atualizar (deve falhar) - 
    update_fail = await async_client.patch("/api/v1/modalidades/1", json={"nome": "Tentativa Fiscal"}, headers=fiscal_headers)
    assert update_fail.status_code == 403

    # Fiscal TENTA deletar (deve falhar) - 
    delete_fail = await async_client.delete("/api/v1/modalidades/1", headers=fiscal_headers)
    assert delete_fail.status_code == 403
    
    print("\n✓ Usuário não-admin foi corretamente bloqueado das rotas de escrita.")