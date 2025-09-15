# tests/test_status_relatorio.py
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
async def test_get_all_status_relatorio(async_client: AsyncClient, admin_headers: Dict):
    """Testa se a lista de status de relatório é retornada corretamente."""
    response = await async_client.get("/statusrelatorio/", headers=admin_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    nomes = [item['nome'] for item in data]
    assert "Pendente de Análise" in nomes
    assert "Aprovado" in nomes
    assert "Rejeitado com Pendência" in nomes

@pytest.mark.asyncio
async def test_get_status_relatorio_by_id(async_client: AsyncClient, admin_headers: Dict):
    """Testa a busca de um status de relatório específico."""
    # Primeiro, pega todos para descobrir um ID válido
    response_all = await async_client.get("/statusrelatorio/", headers=admin_headers)
    item_to_find = response_all.json()[0]
    item_id = item_to_find['id']
    item_name = item_to_find['nome']
    
    response_one = await async_client.get(f"/statusrelatorio/{item_id}", headers=admin_headers)
    assert response_one.status_code == 200
    assert response_one.json()['nome'] == item_name