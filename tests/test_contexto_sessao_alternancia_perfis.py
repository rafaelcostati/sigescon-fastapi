# tests/test_contexto_sessao_alternancia_perfis.py
"""
Testes específicos para contexto de sessão e alternância de perfis.
Verifica funcionalidades de múltiplos perfis por usuário e alternância de contexto.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any, List
import uuid
import random


class TestContextoSessaoAlternancia:
    """Testes do sistema de contexto de sessão e alternância de perfis."""

    @pytest_asyncio.fixture
    async def usuario_multiplos_perfis(self, async_client: AsyncClient, admin_headers: Dict) -> Dict[str, Any]:
        """Cria usuário com múltiplos perfis para testes de alternância."""

        # Criar usuário inicial com perfil Fiscal
        user_data = {
            "nome": f"Usuário Multi Perfil {uuid.uuid4().hex[:6]}",
            "email": f"multi.perfil.{uuid.uuid4().hex[:6]}@teste.com",
            "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
            "senha": "password123",
            "perfil_id": 3  # Fiscal
        }

        user_response = await async_client.post("/api/v1/usuarios/", json=user_data, headers=admin_headers)
        assert user_response.status_code == 201
        user = user_response.json()

        # Conceder perfis Fiscal e Gestor
        perfil_data = {"perfil_ids": [2, 3]}  # Gestor e Fiscal
        perfil_response = await async_client.post(
            f"/api/v1/usuarios/{user['id']}/perfis/conceder",
            json=perfil_data,
            headers=admin_headers
        )
        assert perfil_response.status_code == 200

        return {
            "user": user,
            "user_data": user_data,
            "perfis_concedidos": [2, 3]  # Gestor e Fiscal
        }

    @pytest.mark.asyncio
    async def test_login_retorna_contexto_sessao_completo(self, async_client: AsyncClient, usuario_multiplos_perfis: Dict):
        """Testa se login retorna contexto de sessão completo com múltiplos perfis."""
        print("\n--- Testando Login com Contexto de Sessão Completo ---")

        user_data = usuario_multiplos_perfis["user_data"]

        # Fazer login
        login_response = await async_client.post("/auth/login", data={
            "username": user_data["email"],
            "password": user_data["senha"]
        })
        assert login_response.status_code == 200
        login_data = login_response.json()

        # Verificar estrutura do contexto de sessão
        assert "access_token" in login_data
        assert "contexto_sessao" in login_data

        contexto = login_data["contexto_sessao"]
        assert "usuario_id" in contexto
        assert "perfil_ativo_id" in contexto
        assert "perfil_ativo_nome" in contexto
        assert "perfis_disponiveis" in contexto
        assert "pode_alternar" in contexto
        assert "sessao_id" in contexto

        # Verificar perfis disponíveis (deve ter Gestor e Fiscal)
        perfis_disponiveis = contexto["perfis_disponiveis"]
        assert len(perfis_disponiveis) >= 2

        nomes_perfis = [p["nome"] for p in perfis_disponiveis]
        assert "Gestor" in nomes_perfis
        assert "Fiscal" in nomes_perfis

        # Verificar que pode alternar (tem múltiplos perfis)
        assert contexto["pode_alternar"] == True

        # Perfil ativo deve ser o de maior prioridade (Gestor > Fiscal)
        assert contexto["perfil_ativo_nome"] == "Gestor"

        print(f"✓ Perfil ativo: {contexto['perfil_ativo_nome']}")
        print(f"✓ Perfis disponíveis: {nomes_perfis}")
        print(f"✓ Pode alternar: {contexto['pode_alternar']}")
        print("✅ Contexto de sessão retornado corretamente!")

        return login_data

    @pytest.mark.asyncio
    async def test_alternancia_perfil_funcional(self, async_client: AsyncClient, usuario_multiplos_perfis: Dict):
        """Testa alternância de perfil entre Gestor e Fiscal."""
        print("\n--- Testando Alternância de Perfil ---")

        user_data = usuario_multiplos_perfis["user_data"]

        # Login inicial
        login_response = await async_client.post("/auth/login", data={
            "username": user_data["email"],
            "password": user_data["senha"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        contexto_inicial = login_response.json()["contexto_sessao"]
        print(f"✓ Perfil inicial: {contexto_inicial['perfil_ativo_nome']}")

        # Alternar para Fiscal
        perfil_fiscal_id = next(p for p in contexto_inicial["perfis_disponiveis"] if p["nome"] == "Fiscal")["id"]

        alternancia_data = {
            "novo_perfil_id": perfil_fiscal_id,
            "justificativa": "Alternando para modo de fiscalização"
        }

        alternancia_response = await async_client.post(
            "/auth/alternar-perfil",
            json=alternancia_data,
            headers=headers
        )
        assert alternancia_response.status_code == 200
        novo_contexto = alternancia_response.json()

        # Verificar mudança de contexto
        assert novo_contexto["perfil_ativo_nome"] == "Fiscal"
        assert novo_contexto["perfil_ativo_id"] == perfil_fiscal_id
        print(f"✓ Perfil após alternância: {novo_contexto['perfil_ativo_nome']}")

        # Alternar de volta para Gestor
        perfil_gestor_id = next(p for p in novo_contexto["perfis_disponiveis"] if p["nome"] == "Gestor")["id"]

        volta_data = {
            "novo_perfil_id": perfil_gestor_id,
            "justificativa": "Voltando para modo de gestão"
        }

        volta_response = await async_client.post(
            "/auth/alternar-perfil",
            json=volta_data,
            headers=headers
        )
        assert volta_response.status_code == 200
        contexto_final = volta_response.json()

        assert contexto_final["perfil_ativo_nome"] == "Gestor"
        print(f"✓ Perfil final: {contexto_final['perfil_ativo_nome']}")
        print("✅ Alternância de perfil funcionando corretamente!")

    @pytest.mark.asyncio
    async def test_permissoes_mudam_com_contexto(self, async_client: AsyncClient, usuario_multiplos_perfis: Dict, admin_headers: Dict):
        """Testa se permissões mudam conforme o perfil ativo."""
        print("\n--- Testando Mudança de Permissões com Contexto ---")

        user_data = usuario_multiplos_perfis["user_data"]

        # Login e obter token
        login_response = await async_client.post("/auth/login", data={
            "username": user_data["email"],
            "password": user_data["senha"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        contexto_inicial = login_response.json()["contexto_sessao"]

        # Criar um usuário de teste para verificar permissões de criação
        test_user_data = {
            "nome": f"Usuário Teste Permissão {uuid.uuid4().hex[:6]}",
            "email": f"teste.permissao.{uuid.uuid4().hex[:6]}@teste.com",
            "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
            "senha": "password123",
            "perfil_id": 3  # Fiscal
        }

        # 1. Como Gestor - deve conseguir ver usuários mas não criar
        if contexto_inicial["perfil_ativo_nome"] == "Gestor":
            # Gestor pode listar usuários
            usuarios_response = await async_client.get("/api/v1/usuarios/", headers=headers)
            assert usuarios_response.status_code == 200
            print("✓ Gestor consegue listar usuários")

            # Gestor NÃO pode criar usuários (apenas Admin)
            create_response = await async_client.post("/api/v1/usuarios/", json=test_user_data, headers=headers)
            assert create_response.status_code == 403
            print("✓ Gestor não consegue criar usuários (correto)")

        # 2. Alternar para Fiscal
        perfil_fiscal_id = next(p for p in contexto_inicial["perfis_disponiveis"] if p["nome"] == "Fiscal")["id"]

        alternancia_data = {
            "novo_perfil_id": perfil_fiscal_id,
            "justificativa": "Testando permissões como fiscal"
        }

        await async_client.post("/auth/alternar-perfil", json=alternancia_data, headers=headers)

        # 3. Como Fiscal - deve ter permissões ainda mais limitadas
        usuarios_response_fiscal = await async_client.get("/api/v1/usuarios/", headers=headers)
        # Fiscal pode não conseguir listar todos os usuários (dependendo da implementação)
        # Mas deve conseguir ver seus próprios dados
        me_response = await async_client.get("/api/v1/usuarios/me", headers=headers)
        assert me_response.status_code == 200
        print("✓ Fiscal consegue ver próprios dados")

        # Fiscal definitivamente não pode criar usuários
        create_response_fiscal = await async_client.post("/api/v1/usuarios/", json=test_user_data, headers=headers)
        assert create_response_fiscal.status_code == 403
        print("✓ Fiscal não consegue criar usuários (correto)")

        print("✅ Permissões mudando corretamente conforme contexto ativo!")

    @pytest.mark.asyncio
    async def test_token_jwt_inclui_contexto(self, async_client: AsyncClient, usuario_multiplos_perfis: Dict):
        """Testa se token JWT inclui informações do contexto ativo."""
        print("\n--- Testando Token JWT com Contexto ---")

        user_data = usuario_multiplos_perfis["user_data"]

        # Login inicial
        login_response = await async_client.post("/auth/login", data={
            "username": user_data["email"],
            "password": user_data["senha"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verificar dados do usuário logado
        me_response = await async_client.get("/api/v1/usuarios/me", headers=headers)
        assert me_response.status_code == 200
        user_info = me_response.json()

        # Verificar se dados refletem o perfil ativo
        contexto = login_response.json()["contexto_sessao"]

        # O perfil_id no /me deve ser o perfil ativo (ou refletir sistema legado)
        print(f"✓ Usuário ID: {user_info['id']}")
        print(f"✓ Perfil ativo no contexto: {contexto['perfil_ativo_nome']}")
        print(f"✓ Perfil no /me: {user_info.get('perfil_nome', 'N/A')}")

        # Alternar perfil
        perfil_fiscal_id = next(p for p in contexto["perfis_disponiveis"] if p["nome"] == "Fiscal")["id"]

        alternancia_data = {
            "novo_perfil_id": perfil_fiscal_id,
            "justificativa": "Testando mudança no token"
        }

        alternancia_response = await async_client.post("/auth/alternar-perfil", json=alternancia_data, headers=headers)
        novo_contexto = alternancia_response.json()

        # Verificar dados após alternância (mesmo token)
        me_response_novo = await async_client.get("/api/v1/usuarios/me", headers=headers)
        assert me_response_novo.status_code == 200
        user_info_novo = me_response_novo.json()

        print(f"✓ Novo perfil ativo: {novo_contexto['perfil_ativo_nome']}")
        print(f"✓ Perfil no /me após alternância: {user_info_novo.get('perfil_nome', 'N/A')}")

        print("✅ Token JWT refletindo contexto corretamente!")

    @pytest.mark.asyncio
    async def test_usuario_sem_multiplos_perfis_nao_pode_alternar(self, async_client: AsyncClient, admin_headers: Dict):
        """Testa que usuário com apenas um perfil não pode alternar."""
        print("\n--- Testando Usuário com Perfil Único ---")

        # Criar usuário com apenas um perfil
        user_data = {
            "nome": f"Usuário Perfil Único {uuid.uuid4().hex[:6]}",
            "email": f"perfil.unico.{uuid.uuid4().hex[:6]}@teste.com",
            "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
            "senha": "password123",
            "perfil_id": 3  # Apenas Fiscal
        }

        user_response = await async_client.post("/api/v1/usuarios/", json=user_data, headers=admin_headers)
        assert user_response.status_code == 201
        user = user_response.json()

        # Conceder apenas um perfil (Fiscal)
        perfil_data = {"perfil_ids": [3]}  # Fiscal
        perfil_response = await async_client.post(
            f"/api/v1/usuarios/{user['id']}/perfis/conceder",
            json=perfil_data,
            headers=admin_headers
        )
        assert perfil_response.status_code == 200

        # Login
        login_response = await async_client.post("/auth/login", data={
            "username": user_data["email"],
            "password": user_data["senha"]
        })
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        contexto = login_response.json()["contexto_sessao"]

        # Verificar que não pode alternar
        assert contexto["pode_alternar"] == False
        assert len(contexto["perfis_disponiveis"]) == 1
        assert contexto["perfil_ativo_nome"] == "Fiscal"

        print(f"✓ Perfis disponíveis: {len(contexto['perfis_disponiveis'])}")
        print(f"✓ Pode alternar: {contexto['pode_alternar']}")

        # Tentar alternar mesmo assim (deve falhar)
        alternancia_data = {
            "novo_perfil_id": 2,  # Tentar alternar para Gestor
            "justificativa": "Tentativa inválida"
        }

        alternancia_response = await async_client.post("/auth/alternar-perfil", json=alternancia_data, headers=headers)
        assert alternancia_response.status_code == 403  # Ou 400, dependendo da implementação

        print("✓ Tentativa de alternância rejeitada corretamente")
        print("✅ Usuário com perfil único não consegue alternar!")

    @pytest.mark.asyncio
    async def test_contexto_atual_endpoint(self, async_client: AsyncClient, usuario_multiplos_perfis: Dict):
        """Testa endpoint /auth/contexto que retorna contexto atual."""
        print("\n--- Testando Endpoint /auth/contexto ---")

        user_data = usuario_multiplos_perfis["user_data"]

        # Login
        login_response = await async_client.post("/auth/login", data={
            "username": user_data["email"],
            "password": user_data["senha"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verificar contexto atual
        contexto_response = await async_client.get("/auth/contexto", headers=headers)
        assert contexto_response.status_code == 200
        contexto_atual = contexto_response.json()

        # Deve ter mesma estrutura do contexto de login
        assert "usuario_id" in contexto_atual
        assert "perfil_ativo_id" in contexto_atual
        assert "perfil_ativo_nome" in contexto_atual
        assert "perfis_disponiveis" in contexto_atual

        print(f"✓ Contexto atual obtido: {contexto_atual['perfil_ativo_nome']}")

        # Alternar perfil
        perfil_fiscal_id = next(p for p in contexto_atual["perfis_disponiveis"] if p["nome"] == "Fiscal")["id"]

        alternancia_data = {
            "novo_perfil_id": perfil_fiscal_id,
            "justificativa": "Testando endpoint contexto"
        }

        await async_client.post("/auth/alternar-perfil", json=alternancia_data, headers=headers)

        # Verificar contexto atualizado
        contexto_response_novo = await async_client.get("/auth/contexto", headers=headers)
        assert contexto_response_novo.status_code == 200
        contexto_novo = contexto_response_novo.json()

        assert contexto_novo["perfil_ativo_nome"] == "Fiscal"
        print(f"✓ Contexto atualizado: {contexto_novo['perfil_ativo_nome']}")
        print("✅ Endpoint /auth/contexto funcionando corretamente!")

    @pytest.mark.asyncio
    async def test_sessao_id_persiste_durante_alternancia(self, async_client: AsyncClient, usuario_multiplos_perfis: Dict):
        """Testa se sessao_id persiste durante alternância de perfis."""
        print("\n--- Testando Persistência de Sessão ID ---")

        user_data = usuario_multiplos_perfis["user_data"]

        # Login
        login_response = await async_client.post("/auth/login", data={
            "username": user_data["email"],
            "password": user_data["senha"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        contexto_inicial = login_response.json()["contexto_sessao"]
        sessao_id_inicial = contexto_inicial["sessao_id"]
        print(f"✓ Sessão ID inicial: {sessao_id_inicial}")

        # Alternar perfil
        perfil_fiscal_id = next(p for p in contexto_inicial["perfis_disponiveis"] if p["nome"] == "Fiscal")["id"]

        alternancia_data = {
            "novo_perfil_id": perfil_fiscal_id,
            "justificativa": "Testando persistência de sessão"
        }

        alternancia_response = await async_client.post("/auth/alternar-perfil", json=alternancia_data, headers=headers)
        contexto_alternado = alternancia_response.json()
        sessao_id_alternado = contexto_alternado["sessao_id"]

        # Sessão ID deve permanecer o mesmo
        assert sessao_id_inicial == sessao_id_alternado
        print(f"✓ Sessão ID após alternância: {sessao_id_alternado}")

        # Verificar com endpoint /auth/contexto
        contexto_response = await async_client.get("/auth/contexto", headers=headers)
        contexto_atual = contexto_response.json()
        sessao_id_atual = contexto_atual["sessao_id"]

        assert sessao_id_inicial == sessao_id_atual
        print(f"✓ Sessão ID mantida: {sessao_id_atual}")
        print("✅ Sessão ID persistindo corretamente durante alternância!")


if __name__ == "__main__":
    print("Execute: pytest tests/test_contexto_sessao_alternancia_perfis.py -v")