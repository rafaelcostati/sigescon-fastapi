# tests/test_auth_e_usuarios.py
import pytest
from httpx import AsyncClient
from typing import Dict
import dotenv
import os 

dotenv.load_dotenv()

# Fixture para reutilizar os dados do admin e do usuário comum nos testes
@pytest.fixture(scope="module")
def admin_user_data() -> Dict:
    return {"username": os.getenv("ADMIN_EMAIL"), "password": os.getenv("ADMIN_PASSWORD")}

@pytest.fixture(scope="module")
def common_user_data() -> Dict:
    return {
        "nome": "Usuario Comum Teste",
        "email": "comum@teste.com",
        "cpf": "11122233344",
        "senha": "senha_comum_123",
        "perfil_id": 3  # Fiscal
    }

@pytest.mark.asyncio
async def test_admin_login_and_get_token(async_client: AsyncClient, admin_user_data: Dict):
    """Testa se o admin consegue fazer login e obter um token."""
    print("\n--- Testando Login do Admin ---")
    response = await async_client.post("/auth/login", data=admin_user_data)

    assert response.status_code == 200
    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"
    print("--> Login de Admin bem-sucedido.")

@pytest.mark.asyncio
async def test_admin_can_create_user(async_client: AsyncClient, admin_user_data: Dict, common_user_data: Dict):
    """Testa se um admin autenticado pode criar um novo usuário."""
    print("\n--- Testando Criação de Usuário pelo Admin ---")
    # 1. Obter o token de admin
    login_response = await async_client.post("/auth/login", data=admin_user_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Tentar criar o usuário
    response = await async_client.post("/usuarios/", json=common_user_data, headers=headers)
    
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == common_user_data["email"]
    assert response_data["nome"] == common_user_data["nome"]
    assert "id" in response_data
    print(f"--> Admin criou o usuário '{common_user_data['email']}' com sucesso.")

@pytest.mark.asyncio
async def test_get_current_user_profile(async_client: AsyncClient, admin_user_data: Dict):
    """Testa o endpoint /usuarios/me para retornar o perfil do usuário logado."""
    print("\n--- Testando /usuarios/me ---")
    # 1. Obter o token
    login_response = await async_client.post("/auth/login", data=admin_user_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Acessar o endpoint /me
    response = await async_client.get("/usuarios/me", headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["email"] == admin_user_data["username"]
    print("--> Endpoint /me retornou o perfil correto.")

@pytest.mark.asyncio
async def test_unauthorized_user_cannot_create_user(async_client: AsyncClient, common_user_data: Dict):
    """Testa se um usuário sem token (ou com token não-admin) não pode criar usuários."""
    print("\n--- Testando Bloqueio de Criação de Usuário (Sem Token) ---")
    # Tentativa sem token algum
    response = await async_client.post("/usuarios/", json=common_user_data)
    assert response.status_code == 401  # Unauthorized
    print("--> Rota de criação de usuário bloqueada para acesso sem token.")