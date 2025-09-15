# tests/test_usuarios_complete.py
import pytest
from httpx import AsyncClient
from typing import Dict
import os
import uuid
from dotenv import load_dotenv
import random

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

@pytest.fixture
def unique_user_data() -> Dict:
    """Gera dados únicos para criar um usuário"""
    unique_id = str(uuid.uuid4())[:8]
    cpf_numerico = ''.join([str(random.randint(0, 9)) for _ in range(11)])
    return {
        "nome": f"Teste User {unique_id}",
        "email": f"teste_{unique_id}@example.com",
        "cpf": cpf_numerico,
        "matricula": f"MAT{unique_id}",
        "senha": "senha123",
        "perfil_id": 3  # Fiscal
    }

class TestUsuariosCRUD:
    """Testa o CRUD completo de usuários"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, async_client: AsyncClient, admin_headers: Dict, unique_user_data: Dict):
        """Testa criação de usuário"""
        print("\n--- Testando CREATE de Usuário ---")
        
        response = await async_client.post(
            "/usuarios/",
            json=unique_user_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == unique_user_data["email"]
        assert data["nome"] == unique_user_data["nome"]
        assert "id" in data
        assert data["ativo"] is True
        print(f"✓ Usuário criado: ID {data['id']}")
        
        # Guarda o ID para os próximos testes
        pytest.created_user_id = data["id"]
        pytest.created_user_email = data["email"]
        pytest.created_user_password = unique_user_data["senha"]
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, async_client: AsyncClient, admin_headers: Dict):
        """Testa busca de usuário por ID"""
        print("\n--- Testando GET por ID ---")
        
        user_id = getattr(pytest, "created_user_id", None)
        assert user_id, "Usuário não foi criado no teste anterior"
        
        response = await async_client.get(
            f"/usuarios/{user_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == pytest.created_user_email
        print(f"✓ Usuário {user_id} encontrado")
    
    @pytest.mark.asyncio
    async def test_list_users(self, async_client: AsyncClient, admin_headers: Dict):
        """Testa listagem de usuários"""
        print("\n--- Testando LIST de Usuários ---")
        
        response = await async_client.get("/usuarios/", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ {len(data)} usuários listados")
        
        # Testa filtro por nome
        response = await async_client.get(
            "/usuarios/?nome=Teste",
            headers=admin_headers
        )
        assert response.status_code == 200
        filtered_data = response.json()
        assert all("Teste" in u["nome"] or "teste" in u["nome"].lower() for u in filtered_data)
        print(f"✓ Filtro por nome funcionando")
    
    @pytest.mark.asyncio
    async def test_update_user(self, async_client: AsyncClient, admin_headers: Dict):
        """Testa atualização de usuário"""
        print("\n--- Testando UPDATE de Usuário ---")
        
        user_id = getattr(pytest, "created_user_id", None)
        assert user_id, "Usuário não foi criado"
        
        # Gera uma matrícula única para a atualização
        unique_id_update = str(uuid.uuid4())[:8]
        update_data = {
            "nome": "Nome Atualizado",
            "matricula": f"UPD{unique_id_update}"
        }
        
        response = await async_client.patch(
            f"/usuarios/{user_id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == update_data["nome"]
        assert data["matricula"] == update_data["matricula"]
        assert data["email"] == pytest.created_user_email  # Email não mudou
        print(f"✓ Usuário {user_id} atualizado")
    
    @pytest.mark.asyncio
    async def test_delete_user(self, async_client: AsyncClient, admin_headers: Dict):
        """Testa soft delete de usuário"""
        print("\n--- Testando DELETE de Usuário ---")
        
        user_id = getattr(pytest, "created_user_id", None)
        assert user_id, "Usuário não foi criado"
        
        response = await async_client.delete(
            f"/usuarios/{user_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 204
        print(f"✓ Usuário {user_id} deletado")
        
        # Verifica que o usuário não aparece mais na busca
        response = await async_client.get(
            f"/usuarios/{user_id}",
            headers=admin_headers
        )
        assert response.status_code == 404
        print(f"✓ Usuário não encontrado após delete")


class TestPasswordManagement:
    """Testa funcionalidades de senha"""
    
    @pytest.mark.asyncio
    async def test_user_change_own_password(self, async_client: AsyncClient, admin_headers: Dict, unique_user_data: Dict):
        """Testa alteração de senha pelo próprio usuário"""
        print("\n--- Testando Alteração de Senha ---")
        
        # Cria um usuário novo para este teste
        response = await async_client.post(
            "/usuarios/",
            json=unique_user_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # Faz login com o usuário criado
        login_data = {
            "username": unique_user_data["email"],
            "password": unique_user_data["senha"]
        }
        response = await async_client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        user_token = response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Tenta alterar a própria senha
        password_change = {
            "senha_antiga": unique_user_data["senha"],
            "nova_senha": "nova_senha_123"
        }
        response = await async_client.patch(
            f"/usuarios/{user_id}/alterar-senha",
            json=password_change,
            headers=user_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Senha alterada com sucesso"
        print(f"✓ Senha alterada pelo próprio usuário")
        
        # Verifica que consegue logar com a nova senha
        new_login_data = {
            "username": unique_user_data["email"],
            "password": "nova_senha_123"
        }
        response = await async_client.post("/auth/login", data=new_login_data)
        assert response.status_code == 200
        print(f"✓ Login com nova senha funcionou")
        
        # Limpa o usuário criado
        await async_client.delete(f"/usuarios/{user_id}", headers=admin_headers)
    
    @pytest.mark.asyncio
    async def test_admin_reset_password(self, async_client: AsyncClient, admin_headers: Dict, unique_user_data: Dict):
        """Testa reset de senha por admin"""
        print("\n--- Testando Reset de Senha por Admin ---")
        
        # Cria um usuário para o teste
        response = await async_client.post(
            "/usuarios/",
            json=unique_user_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # Admin reseta a senha
        reset_data = {"nova_senha": "senha_resetada_123"}
        response = await async_client.patch(
            f"/usuarios/{user_id}/resetar-senha",
            json=reset_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert "resetada com sucesso" in response.json()["message"]
        print(f"✓ Senha resetada pelo admin")
        
        # Verifica que consegue logar com a senha resetada
        login_data = {
            "username": unique_user_data["email"],
            "password": "senha_resetada_123"
        }
        response = await async_client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        print(f"✓ Login com senha resetada funcionou")
        
        # Limpa o usuário criado
        await async_client.delete(f"/usuarios/{user_id}", headers=admin_headers)


class TestPermissions:
    """Testa permissões e restrições de acesso"""
    
    @pytest.mark.asyncio
    async def test_non_admin_cannot_create_user(self, async_client: AsyncClient, unique_user_data: Dict, admin_headers: Dict):
        """Testa que usuário comum não pode criar outros usuários"""
        print("\n--- Testando Restrições de Permissão ---")
        
        # Cria um usuário fiscal
        fiscal_data = unique_user_data.copy()
        fiscal_data["perfil_id"] = 3  # Fiscal
        response = await async_client.post(
            "/usuarios/",
            json=fiscal_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        fiscal_id = response.json()["id"]
        
        # Faz login como fiscal
        login_data = {
            "username": fiscal_data["email"],
            "password": fiscal_data["senha"]
        }
        response = await async_client.post("/auth/login", data=login_data)
        fiscal_token = response.json()["access_token"]
        fiscal_headers = {"Authorization": f"Bearer {fiscal_token}"}
        
        # Tenta criar outro usuário (deve falhar)
        new_user_data = unique_user_data.copy()
        new_user_data["email"] = "outro@example.com"
        new_user_data["cpf"] = ''.join([str(random.randint(0, 9)) for _ in range(11)])
        response = await async_client.post(
            "/usuarios/",
            json=new_user_data,
            headers=fiscal_headers
        )
        
        assert response.status_code == 403
        print(f"✓ Fiscal bloqueado de criar usuários")
        
        # Limpa
        await async_client.delete(f"/usuarios/{fiscal_id}", headers=admin_headers)
    
    @pytest.mark.asyncio
    async def test_user_cannot_change_others_password(self, async_client: AsyncClient, admin_headers: Dict):
        """Testa que usuário não pode alterar senha de outros"""
        print("\n--- Testando Proteção de Senha ---")
        
        # Cria dois usuários
        user1_data = {
            "nome": "User 1",
            "email": f"user1_{uuid.uuid4().hex[:8]}@test.com",
            "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
            "senha": "senha1",
            "perfil_id": 3
        }
        user2_data = {
            "nome": "User 2",
            "email": f"user2_{uuid.uuid4().hex[:8]}@test.com",
            "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
            "senha": "senha2",
            "perfil_id": 3
        }
        
        # Cria ambos
        response1 = await async_client.post("/usuarios/", json=user1_data, headers=admin_headers)
        response2 = await async_client.post("/usuarios/", json=user2_data, headers=admin_headers)
        assert response1.status_code == 201
        assert response2.status_code == 201
        user1_id = response1.json()["id"]
        user2_id = response2.json()["id"]
        
        # Login como user1
        login_data = {"username": user1_data["email"], "password": user1_data["senha"]}
        response = await async_client.post("/auth/login", data=login_data)
        user1_token = response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        # User1 tenta alterar senha do User2 (deve falhar)
        password_change = {
            "senha_antiga": "qualquer",
            "nova_senha": "hackeada"
        }
        response = await async_client.patch(
            f"/usuarios/{user2_id}/alterar-senha",
            json=password_change,
            headers=user1_headers
        )
        
        assert response.status_code == 403
        print(f"✓ Usuário impedido de alterar senha de outros")
        
        # Limpa
        await async_client.delete(f"/usuarios/{user1_id}", headers=admin_headers)
        await async_client.delete(f"/usuarios/{user2_id}", headers=admin_headers)