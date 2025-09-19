# tests/test_pendencias.py 
import pytest
from httpx import AsyncClient
from typing import Dict, Any
import os
from dotenv import load_dotenv
import uuid
import random
from datetime import date

load_dotenv()

# --- Fixtures de Autenticação e Pré-requisitos ---

@pytest.fixture
def admin_credentials() -> Dict:
    return {"username": os.getenv("ADMIN_EMAIL"), "password": os.getenv("ADMIN_PASSWORD")}

@pytest.fixture
async def admin_user_id(async_client: AsyncClient, admin_headers: Dict) -> int:
    """Obtém o ID do usuário admin logado."""
    response = await async_client.get("/api/v1/usuarios/me", headers=admin_headers)  
    assert response.status_code == 200
    return response.json()["id"]

@pytest.fixture
async def admin_headers(async_client: AsyncClient, admin_credentials: Dict) -> Dict:
    response = await async_client.post("/auth/login", data=admin_credentials)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def setup_contract(async_client: AsyncClient, admin_headers: Dict, admin_user_id: int) -> Dict[str, Any]:
    """Cria um contrato completo e retorna seus dados e IDs."""
    
    # Cria um usuário fiscal para o contrato
    fiscal_data = {
        "nome": f"Fiscal Pendencia Teste {uuid.uuid4().hex[:6]}",
        "email": f"fiscal.pendencia.{uuid.uuid4().hex[:6]}@teste.com",
        "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
        "senha": "password123", "perfil_id": 3
    }
    fiscal_resp = await async_client.post("/api/v1/usuarios/", json=fiscal_data, headers=admin_headers)
    fiscal = fiscal_resp.json()

    # Conceder perfil fiscal via sistema de múltiplos perfis
    perfil_data = {"perfil_ids": [3]}  # Fiscal
    perfil_response = await async_client.post(
        f"/api/v1/usuarios/{fiscal['id']}/perfis/conceder",
        json=perfil_data,
        headers=admin_headers
    )
    assert perfil_response.status_code == 200

    # Cria um contratado
    contratado_data = {
        "nome": f"Empresa Pendencia Teste {uuid.uuid4().hex[:6]}",
        "email": f"empresa.pendencia.{uuid.uuid4().hex[:6]}@teste.com"
    }
    contratado_resp = await async_client.post("/api/v1/contratados/", json=contratado_data, headers=admin_headers)  
    contratado = contratado_resp.json()

    # Pega IDs de dados semeados
    modalidades_resp = await async_client.get("/api/v1/modalidades/", headers=admin_headers)  
    status_resp = await async_client.get("/api/v1/status/", headers=admin_headers)  

    # Cria o contrato
    contrato_data = {
        "nr_contrato": f"PEND-{uuid.uuid4().hex[:8]}",
        "objeto": "Contrato para teste de pendências",
        "data_inicio": str(date(2025, 1, 1)), 
        "data_fim": str(date(2025, 12, 31)),
        "contratado_id": contratado['id'],
        "modalidade_id": modalidades_resp.json()[0]['id'],
        "status_id": status_resp.json()[0]['id'],
        "gestor_id": fiscal['id'],  # Usando o fiscal como gestor para simplificar
        "fiscal_id": fiscal['id']
    }
    
    # Enviando como 'data' para corresponder ao endpoint de formulário
    contrato_resp = await async_client.post("/api/v1/contratos/", data=contrato_data, headers=admin_headers)  
    
    assert contrato_resp.status_code == 201
    contrato = contrato_resp.json()

    # Obter o token do fiscal
    login_resp = await async_client.post('/auth/login', data={'username': fiscal['email'], 'password': 'password123'})
    fiscal_token = login_resp.json()['access_token']

    return {
        "contrato_id": contrato['id'],
        "admin_id": admin_user_id,
        "fiscal_headers": {"Authorization": f"Bearer {fiscal_token}"}
    }

# --- Suite de Testes para Pendências ---

@pytest.mark.asyncio
async def test_pendencia_workflow(async_client: AsyncClient, admin_headers: Dict, setup_contract: Dict):
    """Testa a criação e listagem de pendências."""
    
    contrato_id = setup_contract["contrato_id"]
    admin_id = setup_contract["admin_id"]
    fiscal_headers = setup_contract["fiscal_headers"]

    # Pega o ID de um status de pendência válido
    status_pendencia_resp = await async_client.get("/api/v1/statuspendencia/", headers=admin_headers)  
    status_pendente_id = next(s for s in status_pendencia_resp.json() if s['nome'] == 'Pendente')['id']

    # 1. Fiscal tenta criar pendência (deve falhar)
    pendencia_data_fail = {
        "descricao": "Tentativa de criação pelo fiscal",
        "data_prazo": str(date(2025, 2, 28)),
        "status_pendencia_id": status_pendente_id,
        "criado_por_usuario_id": admin_id
    }
    create_fail_resp = await async_client.post(f"/api/v1/contratos/{contrato_id}/pendencias/", json=pendencia_data_fail, headers=fiscal_headers)  
    assert create_fail_resp.status_code == 403

    # 2. Admin cria a pendência (deve funcionar)
    pendencia_data_ok = {
        "descricao": "Relatório mensal de atividades",
        "data_prazo": str(date(2025, 3, 31)),
        "status_pendencia_id": status_pendente_id,
        "criado_por_usuario_id": admin_id
    }
    create_ok_resp = await async_client.post(f"/api/v1/contratos/{contrato_id}/pendencias/", json=pendencia_data_ok, headers=admin_headers)  
    assert create_ok_resp.status_code == 201
    created_pendencia = create_ok_resp.json()
    assert created_pendencia["descricao"] == pendencia_data_ok["descricao"]
    assert created_pendencia["criado_por_nome"] is not None

    # 3. Fiscal lista as pendências do contrato (deve funcionar)
    list_resp = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=fiscal_headers)  
    assert list_resp.status_code == 200
    pendencias_list = list_resp.json()
    assert len(pendencias_list) == 1
    assert pendencias_list[0]["id"] == created_pendencia["id"]