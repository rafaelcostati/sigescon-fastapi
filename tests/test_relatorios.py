# tests/test_relatorios.py
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
async def admin_headers(async_client: AsyncClient) -> Dict:
    response = await async_client.post("/auth/login", data={
        "username": os.getenv("ADMIN_EMAIL"),
        "password": os.getenv("ADMIN_PASSWORD")
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def admin_user(async_client: AsyncClient, admin_headers: Dict) -> Dict:
    response = await async_client.get("/api/v1/usuarios/me", headers=admin_headers)
    return response.json()

@pytest.fixture
async def setup_for_reports(async_client: AsyncClient, admin_headers: Dict, admin_user: Dict) -> Dict:
    """Cria um fiscal, um contrato e uma pendência para os testes de relatório."""
    
    # 1. Criar um usuário Fiscal
    fiscal_data = {
        "nome": f"Fiscal Relatorio Teste {uuid.uuid4().hex[:6]}",
        "email": f"fiscal.relatorio.{uuid.uuid4().hex[:6]}@teste.com",
        "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
        "senha": "password123", "perfil_id": 3
    }
    fiscal_resp = await async_client.post("/api/v1/usuarios/", json=fiscal_data, headers=admin_headers)
    assert fiscal_resp.status_code == 201, f"Falha ao criar usuário fiscal: {fiscal_resp.text}"
    fiscal = fiscal_resp.json()

    # Conceder perfil fiscal via sistema de múltiplos perfis
    perfil_data = {"perfil_ids": [3]}  # Fiscal
    perfil_response = await async_client.post(
        f"/api/v1/usuarios/{fiscal['id']}/perfis/conceder",
        json=perfil_data,
        headers=admin_headers
    )
    assert perfil_response.status_code == 200

    # Login do fiscal para obter token
    fiscal_login = await async_client.post('/auth/login', data={'username': fiscal['email'], 'password': 'password123'})
    fiscal_token = fiscal_login.json()['access_token']
    fiscal_headers = {"Authorization": f"Bearer {fiscal_token}"}

    # 2. Criar um Contrato
    contratado_resp = await async_client.post("/api/v1/contratados/", json={"nome": f"Empresa Relatorio {uuid.uuid4().hex[:6]}", "email": f"empresa.relatorio.{uuid.uuid4().hex[:6]}@teste.com"}, headers=admin_headers)
    contratado = contratado_resp.json()
    modalidades_resp = await async_client.get("/api/v1/modalidades/", headers=admin_headers)
    status_resp = await async_client.get("/api/v1/status/", headers=admin_headers)

    contrato_data = {
        "nr_contrato": f"REL-{uuid.uuid4().hex[:8]}", "objeto": "Contrato para teste de relatórios",
        "data_inicio": str(date(2025, 1, 1)), "data_fim": str(date(2025, 12, 31)),
        "contratado_id": contratado['id'], "modalidade_id": modalidades_resp.json()[0]['id'],
        "status_id": status_resp.json()[0]['id'], "gestor_id": fiscal['id'], "fiscal_id": fiscal['id']
    }
    contrato_resp = await async_client.post("/api/v1/contratos/", data=contrato_data, headers=admin_headers)
    contrato = contrato_resp.json()

    # 3. Criar uma Pendência
    status_pendencia_resp = await async_client.get("/api/v1/statuspendencia/", headers=admin_headers)
    status_pendente_id = next(s for s in status_pendencia_resp.json() if s['nome'] == 'Pendente')['id']
    
    pendencia_data = {
        "descricao": "Primeiro relatório de atividades", "data_prazo": str(date(2025, 2, 28)),
        "status_pendencia_id": status_pendente_id, "criado_por_usuario_id": admin_user['id']
    }
    pendencia_resp = await async_client.post(f"/api/v1/contratos/{contrato['id']}/pendencias/", json=pendencia_data, headers=admin_headers)
    pendencia = pendencia_resp.json()

    return {
        "contrato_id": contrato['id'],
        "pendencia_id": pendencia['id'],
        "admin_user_id": admin_user['id'],
        "fiscal_headers": fiscal_headers,
    }

# --- Suite de Testes para Relatórios ---

@pytest.mark.asyncio
async def test_full_report_workflow(async_client: AsyncClient, admin_headers: Dict, setup_for_reports: Dict):
    """Testa o fluxo completo: submissão de relatório pelo fiscal e análise pelo admin."""
    
    contrato_id = setup_for_reports["contrato_id"]
    pendencia_id = setup_for_reports["pendencia_id"]
    admin_id = setup_for_reports["admin_user_id"]
    fiscal_headers = setup_for_reports["fiscal_headers"]

    # 1. Fiscal submete o relatório
    report_data = {
        "mes_competencia": str(date(2025, 1, 31)),
        "pendencia_id": str(pendencia_id),
        "observacoes_fiscal": "Primeiro relatório submetido."
    }
    files = {"arquivo": ("relatorio_jan.txt", "Conteúdo do relatório.", "text/plain")}
    
    submit_resp = await async_client.post(
        f"/api/v1/contratos/{contrato_id}/relatorios/",
        data=report_data,
        files=files,
        headers=fiscal_headers
    )
    assert submit_resp.status_code == 201
    submitted_report = submit_resp.json()
    assert submitted_report["pendencia_id"] == pendencia_id
    assert submitted_report["status_relatorio"] == "Pendente de Análise"

    relatorio_id = submitted_report["id"]

    # 2. Admin analisa e aprova o relatório
    status_aprovado_resp = await async_client.get("/api/v1/statusrelatorio/", headers=admin_headers)
    status_aprovado_id = next(s for s in status_aprovado_resp.json() if s['nome'] == 'Aprovado')['id']

    analise_data = {
        "aprovador_usuario_id": admin_id,
        "status_id": status_aprovado_id,
        "observacoes_aprovador": "Relatório aprovado."
    }
    
    analise_resp = await async_client.patch(
        f"/api/v1/contratos/{contrato_id}/relatorios/{relatorio_id}/analise",
        json=analise_data,
        headers=admin_headers
    )
    assert analise_resp.status_code == 200
    approved_report = analise_resp.json()
    assert approved_report["status_relatorio"] == "Aprovado"