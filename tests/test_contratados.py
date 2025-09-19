# tests/test_contratados.py 
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict
import os
from dotenv import load_dotenv
import random

load_dotenv()

@pytest_asyncio.fixture(scope="module")
def admin_credentials() -> Dict:
    return {"username": os.getenv("ADMIN_EMAIL"), "password": os.getenv("ADMIN_PASSWORD")}

@pytest_asyncio.fixture
async def admin_token(async_client: AsyncClient, admin_credentials: Dict) -> str:
    response = await async_client.post("/auth/login", data=admin_credentials)
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def admin_headers(admin_token: str) -> Dict:
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.mark.asyncio
async def test_full_crud_workflow(async_client: AsyncClient, admin_headers: Dict):
    """
    Testa o fluxo completo de CRUD (Create, Read, Update, Delete)
    para o endpoint de contratados em uma única função para garantir a ordem.
    
    AGORA: Estas rotas requerem autenticação de administrador.
    """
    # Gera um identificador único para este teste
    unique_num = str(random.randint(10000000, 99999999))  # 8 dígitos
    
    # --- 1. CREATE (POST /contratados) ---
    print("\n--- Testando CREATE ---")
    create_data = {
        "nome": f"Contratado Teste {unique_num} LTDA",
        "email": f"teste_{unique_num}@example.com",
        "cnpj": f"{unique_num}000199",  # CNPJ de 14 dígitos
        "cpf": None,
        "telefone": "91988887777"
    }
    response = await async_client.post("/api/v1/contratados/", json=create_data, headers=admin_headers)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == create_data["email"]
    assert response_data["nome"] == create_data["nome"]
    assert "id" in response_data
    contratado_id = response_data["id"]
    print(f"--> Contratado ID {contratado_id} criado com sucesso.")

    # --- 2. READ ONE (GET /contratados/{id}) ---
    print("\n--- Testando READ ONE ---")
    response = await async_client.get(f"/api/v1/contratados/{contratado_id}", headers=admin_headers)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == contratado_id
    assert response_data["nome"] == create_data["nome"]
    print(f"--> Contratado ID {contratado_id} lido com sucesso.")

    # --- 3. READ ALL (GET /contratados) ---
    print("\n--- Testando READ ALL ---")
    response = await async_client.get("/api/v1/contratados/", headers=admin_headers)

    assert response.status_code == 200
    response_data = response.json()
    
    # A resposta agora é paginada, então verificamos a estrutura
    assert "data" in response_data
    assert "total_items" in response_data
    assert isinstance(response_data["data"], list)
    assert len(response_data["data"]) > 0
    
    # Verifica se o ID que acabamos de criar está na lista
    contratado_ids = [c["id"] for c in response_data["data"]]
    assert contratado_id in contratado_ids
    print(f"--> Lista de contratados lida com sucesso.")

    # --- 4. UPDATE (PATCH /contratados/{id}) ---
    print("\n--- Testando UPDATE ---")
    update_data = {
        "nome": f"Nome Atualizado {unique_num} SA",
        "telefone": "91955554444"
    }
    response = await async_client.patch(f"/api/v1/contratados/{contratado_id}", json=update_data, headers=admin_headers)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["nome"] == update_data["nome"]
    assert response_data["telefone"] == update_data["telefone"]
    assert response_data["email"] == create_data["email"]  # Garante que o email não mudou
    print(f"--> Contratado ID {contratado_id} atualizado com sucesso.")

    # --- 5. DELETE (DELETE /contratados/{id}) ---
    print("\n--- Testando DELETE ---")
    response = await async_client.delete(f"/api/v1/contratados/{contratado_id}", headers=admin_headers)

    assert response.status_code == 204  # No Content

    # --- 6. VERIFY DELETE ---
    print("\n--- Verificando DELETE ---")
    response = await async_client.get(f"/api/v1/contratados/{contratado_id}", headers=admin_headers)

    assert response.status_code == 404  # Not Found
    print(f"--> Contratado ID {contratado_id} deletado e não é mais encontrado.")

@pytest.mark.asyncio
async def test_unauthorized_access_blocked(async_client: AsyncClient):
    """Testa que usuários não autenticados não podem acessar as rotas de contratados."""
    print("\n--- Testando Bloqueio de Acesso Não Autorizado ---")
    
    # Tenta criar sem token
    create_data = {
        "nome": "Teste Sem Auth",
        "email": "teste@example.com"
    }
    response = await async_client.post("/api/v1/contratados/", json=create_data)
    assert response.status_code == 401  # Unauthorized
    
    # Tenta listar sem token  
    response = await async_client.get("/api/v1/contratados/")
    assert response.status_code == 401  # Unauthorized
    
    print("--> Acesso não autorizado corretamente bloqueado.")

@pytest.mark.asyncio
async def test_non_admin_user_blocked(async_client: AsyncClient, admin_headers: Dict):
    """Testa que usuários não-admin não podem criar/editar/deletar contratados."""
    print("\n--- Testando Bloqueio de Usuário Não-Admin ---")
    
    # Primeiro cria um usuário fiscal para teste
    fiscal_data = {
        "nome": "Fiscal Teste Contratados",
        "email": f"fiscal.contratados.{random.randint(1000, 9999)}@teste.com",
        "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
        "senha": "password123",
        "perfil_id": 3  # Fiscal
    }
    
    create_user_response = await async_client.post("/api/v1/usuarios/", json=fiscal_data, headers=admin_headers)
    assert create_user_response.status_code == 201
    fiscal_id = create_user_response.json()["id"]

    # Conceder perfil fiscal via sistema de múltiplos perfis
    perfil_data = {"perfil_ids": [3]}  # Fiscal
    perfil_response = await async_client.post(
        f"/api/v1/usuarios/{fiscal_id}/perfis/conceder",
        json=perfil_data,
        headers=admin_headers
    )
    assert perfil_response.status_code == 200

    # Login como fiscal
    login_response = await async_client.post("/auth/login", data={"username": fiscal_data["email"], "password": fiscal_data["senha"]})
    assert login_response.status_code == 200
    fiscal_token = login_response.json()["access_token"]
    fiscal_headers = {"Authorization": f"Bearer {fiscal_token}"}
    
    # Fiscal PODE ler (acesso básico)
    read_response = await async_client.get("/api/v1/contratados/", headers=fiscal_headers)
    assert read_response.status_code == 200  # Leitura permitida
    
    # Verifica se a resposta tem a estrutura de paginação
    response_data = read_response.json()
    assert "data" in response_data
    assert "total_items" in response_data
    
    # Fiscal NÃO PODE criar
    create_attempt = await async_client.post("/api/v1/contratados/", json={"nome": "Tentativa", "email": "tentativa@teste.com"}, headers=fiscal_headers)
    assert create_attempt.status_code == 403  # Forbidden
    
    # Fiscal NÃO PODE atualizar (assumindo que existe contratado ID 1)
    update_attempt = await async_client.patch("/api/v1/contratados/1", json={"nome": "Tentativa Update"}, headers=fiscal_headers)
    assert update_attempt.status_code == 403  # Forbidden
    
    # Fiscal NÃO PODE deletar
    delete_attempt = await async_client.delete("/api/v1/contratados/1", headers=fiscal_headers)
    assert delete_attempt.status_code == 403  # Forbidden
    
    print("--> Usuário não-admin corretamente bloqueado das operações de escrita.")
    
    # Limpa o usuário de teste
    await async_client.delete(f"/api/v1/usuarios/{fiscal_id}", headers=admin_headers)