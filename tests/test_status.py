# tests/test_status.py
import pytest
from httpx import AsyncClient
from typing import Dict
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

# Fixtures movidas para conftest.py

@pytest.mark.asyncio
async def test_crud_status_workflow(async_client: AsyncClient, admin_headers: Dict):
    """Testa o fluxo completo de CRUD para Status de Contratos."""
    
    unique_name = f"Status Teste {uuid.uuid4().hex[:6]}"
    
    # 1. CREATE
    create_response = await async_client.post(
        "/api/v1/status/",
        json={"nome": unique_name},
        headers=admin_headers
    )
    assert create_response.status_code == 201
    created_data = create_response.json()
    assert created_data["nome"] == unique_name
    status_id = created_data["id"]

    # 2. READ ALL
    get_all_response = await async_client.get("/api/v1/status/", headers=admin_headers)
    assert get_all_response.status_code == 200
    status_list = get_all_response.json()
    assert isinstance(status_list, list)
    assert unique_name in [s["nome"] for s in status_list]

    # 3. UPDATE
    updated_name = f"Status Atualizado {uuid.uuid4().hex[:6]}"
    update_response = await async_client.patch(
        f"/api/v1/status/{status_id}",
        json={"nome": updated_name},
        headers=admin_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["nome"] == updated_name

    # 4. DELETE
    delete_response = await async_client.delete(f"/api/v1/status/{status_id}", headers=admin_headers)
    assert delete_response.status_code == 204

    # 5. VERIFY DELETE
    verify_response = await async_client.get("/api/v1/status/", headers=admin_headers)
    assert updated_name not in [s["nome"] for s in verify_response.json()]

@pytest.mark.asyncio
async def test_get_seeded_status(async_client: AsyncClient, admin_headers: Dict):
    """Verifica se os status criados pelo seeder estão presentes."""
    response = await async_client.get("/api/v1/status/", headers=admin_headers)
    assert response.status_code == 200
    status_list = [s['nome'] for s in response.json()]
    assert "Ativo" in status_list
    assert "Encerrado" in status_list