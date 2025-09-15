# tests/test_perfis.py
import pytest
from httpx import AsyncClient
from typing import Dict
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente para os testes
load_dotenv()

@pytest.fixture(scope="module")
def admin_credentials() -> Dict:
    """Credenciais do admin do .env"""
    return {
        "username": os.getenv("ADMIN_EMAIL"),
        "password": os.getenv("ADMIN_PASSWORD")
    }

@pytest.fixture
async def admin_token(async_client: AsyncClient, admin_credentials: Dict) -> str:
    """Obtém um token de admin válido"""
    response = await async_client.post("/auth/login", data=admin_credentials)
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
async def admin_headers(admin_token: str) -> Dict:
    """Headers com autenticação de admin"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.mark.asyncio
async def test_get_all_perfis(async_client: AsyncClient, admin_headers: dict):
    """Testa a listagem de todos os perfis por um usuário autenticado."""
    response = await async_client.get("/perfis/", headers=admin_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    # Verifica se os perfis semeados no banco de dados estão presentes
    nomes_perfis = [p["nome"] for p in data]
    assert "Administrador" in nomes_perfis
    assert "Fiscal" in nomes_perfis
    assert "Gestor" in nomes_perfis

@pytest.mark.asyncio
async def test_admin_can_create_perfil(async_client: AsyncClient, admin_headers: dict):
    """Testa se um admin pode criar um novo perfil."""
    new_perfil = {"nome": "Perfil de Teste Automatizado"}
    response = await async_client.post("/perfis/", json=new_perfil, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["nome"] == new_perfil["nome"]
    assert "id" in response.json()