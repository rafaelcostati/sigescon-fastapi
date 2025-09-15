# tests/test_status_pendencia.py
import pytest
from httpx import AsyncClient
from typing import Dict
import os
from dotenv import load_dotenv

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
async def test_get_all_status_pendencia(async_client: AsyncClient, admin_headers: Dict):
    """Testa se a lista de status de pendência é retornada corretamente."""
    response = await async_client.get("/statuspendencia/", headers=admin_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    nomes = [item['nome'] for item in data]
    assert "Pendente" in nomes
    assert "Concluída" in nomes
    assert "Cancelada" in nomes

@pytest.mark.asyncio
async def test_get_status_pendencia_by_id(async_client: AsyncClient, admin_headers: Dict):
    """Testa a busca de um status de pendência específico."""
    response_all = await async_client.get("/statuspendencia/", headers=admin_headers)
    item_to_find = next(item for item in response_all.json() if item['nome'] == 'Pendente')
    item_id = item_to_find['id']
    
    response_one = await async_client.get(f"/statuspendencia/{item_id}", headers=admin_headers)
    assert response_one.status_code == 200
    assert response_one.json()['nome'] == 'Pendente'