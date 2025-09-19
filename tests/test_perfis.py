# tests/test_perfis.py 
import pytest
from httpx import AsyncClient
from typing import Dict
import os
from dotenv import load_dotenv
import uuid

# Carrega as variáveis de ambiente para os testes
load_dotenv()

# Fixtures movidas para conftest.py

# admin_headers também está no conftest.py


@pytest.mark.asyncio
async def test_get_all_perfis(async_client: AsyncClient, admin_headers: dict):
    """Testa a listagem de todos os perfis por um usuário autenticado."""
    response = await async_client.get("/api/v1/perfis/", headers=admin_headers)
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
    unique_name = f"Perfil Teste {uuid.uuid4().hex[:6]}"
    new_perfil = {"nome": unique_name}
    
    response = await async_client.post("/api/v1/perfis/", json=new_perfil, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["nome"] == new_perfil["nome"]
    assert "id" in response.json()