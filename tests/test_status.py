# tests/test_status.py
import pytest
from httpx import AsyncClient
from typing import Dict
import os
from dotenv import load_dotenv
import uuid

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
async def test_crud_status_workflow(async_client: AsyncClient, admin_headers: Dict):
    """Testa o fluxo completo de CRUD para Status de Contratos."""
    
    unique_name = f"Status Teste {uuid.uuid4().hex[:6]}"
    
    # 1. CREATE
    create_response = await async_client.post(
        "/status/",
        json={"nome": unique_name},
        headers=admin_headers
    )
    assert create_response.status_code == 201
    created_data = create_response.json()
    assert created_data["nome"] == unique_name
    status_id = created_data["id"]

    # 2. READ ALL
    get_all_response = await async_client.get("/status/", headers=admin_headers)
    assert get_all_response.status_code == 200
    status_list = get_all_response.json()
    assert isinstance(status_list, list)
    assert unique_name in [s["nome"] for s in status_list]

    # 3. UPDATE
    updated_name = f"Status Atualizado {uuid.uuid4().hex[:6]}"
    update_response = await async_client.patch(
        f"/status/{status_id}",
        json={"nome": updated_name},
        headers=admin_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["nome"] == updated_name

    # 4. DELETE
    delete_response = await async_client.delete(f"/status/{status_id}", headers=admin_headers)
    assert delete_response.status_code == 204

    # 5. VERIFY DELETE
    verify_response = await async_client.get("/status/", headers=admin_headers)
    assert updated_name not in [s["nome"] for s in verify_response.json()]

@pytest.mark.asyncio
async def test_get_seeded_status(async_client: AsyncClient, admin_headers: Dict):
    """Verifica se os status criados pelo seeder estão presentes."""
    response = await async_client.get("/status/", headers=admin_headers)
    assert response.status_code == 200
    status_list = [s['nome'] for s in response.json()]
    assert "Vigente" in status_list
    assert "Encerrado" in status_list