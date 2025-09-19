# tests/test_workflow_relatorios.py
import pytest
from httpx import AsyncClient
from typing import Dict, Any
import os
from dotenv import load_dotenv
import uuid
import random
from datetime import date

load_dotenv()

# --- Fixtures ---

@pytest.fixture
async def admin_headers(async_client: AsyncClient) -> Dict:
    response = await async_client.post("/auth/login", data={
        "username": os.getenv("ADMIN_EMAIL"),
        "password": os.getenv("ADMIN_PASSWORD")
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def setup_complete_workflow(async_client: AsyncClient, admin_headers: Dict) -> Dict[str, Any]:
    """Cria um ambiente completo para testar o workflow de relatórios."""

    # Criar usuário fiscal
    fiscal_data = {
        "nome": f"Fiscal Workflow {uuid.uuid4().hex[:6]}",
        "email": f"fiscal.workflow.{uuid.uuid4().hex[:6]}@teste.com",
        "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
        "senha": "password123",
        "perfil_id": 3
    }
    fiscal_resp = await async_client.post("/api/v1/usuarios/", json=fiscal_data, headers=admin_headers)
    fiscal = fiscal_resp.json()

    # Conceder perfil fiscal
    perfil_data = {"perfil_ids": [3]}
    await async_client.post(
        f"/api/v1/usuarios/{fiscal['id']}/perfis/conceder",
        json=perfil_data,
        headers=admin_headers
    )

    # Criar contratado
    contratado_resp = await async_client.post("/api/v1/contratados/", json={
        "nome": f"Empresa Workflow {uuid.uuid4().hex[:6]}",
        "email": f"empresa.workflow.{uuid.uuid4().hex[:6]}@teste.com"
    }, headers=admin_headers)
    contratado = contratado_resp.json()

    # Obter dados auxiliares
    modalidades_resp = await async_client.get("/api/v1/modalidades/", headers=admin_headers)
    status_resp = await async_client.get("/api/v1/status/", headers=admin_headers)

    # Criar contrato
    contrato_data = {
        "nr_contrato": f"WF-{uuid.uuid4().hex[:8]}",
        "objeto": "Contrato para teste de workflow",
        "data_inicio": str(date(2025, 1, 1)),
        "data_fim": str(date(2025, 12, 31)),
        "contratado_id": contratado['id'],
        "modalidade_id": modalidades_resp.json()[0]['id'],
        "status_id": status_resp.json()[0]['id'],
        "gestor_id": fiscal['id'],
        "fiscal_id": fiscal['id']
    }

    contrato_resp = await async_client.post(
        "/api/v1/contratos/",
        data=contrato_data,
        headers=admin_headers
    )
    contrato = contrato_resp.json()

    # Login do fiscal
    fiscal_login = await async_client.post('/auth/login', data={
        'username': fiscal['email'],
        'password': 'password123'
    })
    fiscal_headers = {"Authorization": f"Bearer {fiscal_login.json()['access_token']}"}

    # Obter ID do usuário admin
    admin_user_resp = await async_client.get("/api/v1/usuarios/me", headers=admin_headers)
    admin_user = admin_user_resp.json()

    return {
        "contrato_id": contrato['id'],
        "fiscal_id": fiscal['id'],
        "fiscal_headers": fiscal_headers,
        "admin_user_id": admin_user['id']
    }

# --- Testes de Workflow Completo ---

@pytest.mark.asyncio
async def test_workflow_completo_pendencia_relatorio(async_client: AsyncClient, admin_headers: Dict, setup_complete_workflow: Dict):
    """Testa o workflow completo: Pendência → Relatório → Análise → Aprovação."""

    contrato_id = setup_complete_workflow["contrato_id"]
    fiscal_headers = setup_complete_workflow["fiscal_headers"]
    admin_user_id = setup_complete_workflow["admin_user_id"]

    # 1. Admin cria pendência
    status_pendencia_resp = await async_client.get("/api/v1/statuspendencia/", headers=admin_headers)
    status_pendente_id = next(s for s in status_pendencia_resp.json() if s['nome'] == 'Pendente')['id']

    pendencia_data = {
        "descricao": "Relatório fiscal de janeiro",
        "data_prazo": str(date(2025, 2, 15)),
        "status_pendencia_id": status_pendente_id,
        "criado_por_usuario_id": admin_user_id
    }

    pendencia_resp = await async_client.post(
        f"/api/v1/contratos/{contrato_id}/pendencias/",
        json=pendencia_data,
        headers=admin_headers
    )
    assert pendencia_resp.status_code == 201
    pendencia = pendencia_resp.json()
    assert pendencia["status_nome"] == "Pendente"

    pendencia_id = pendencia["id"]

    # 2. Fiscal submete relatório
    relatorio_data = {
        "mes_competencia": str(date(2025, 1, 31)),
        "pendencia_id": str(pendencia_id),
        "observacoes_fiscal": "Relatório de atividades de janeiro"
    }
    files = {"arquivo": ("relatorio_janeiro.pdf", "Conteúdo do relatório PDF", "application/pdf")}

    relatorio_resp = await async_client.post(
        f"/api/v1/contratos/{contrato_id}/relatorios/",
        data=relatorio_data,
        files=files,
        headers=fiscal_headers
    )
    assert relatorio_resp.status_code == 201
    relatorio = relatorio_resp.json()
    assert relatorio["status_relatorio"] == "Pendente de Análise"

    relatorio_id = relatorio["id"]

    # 3. Admin aprova o relatório
    status_relatorio_resp = await async_client.get("/api/v1/statusrelatorio/", headers=admin_headers)
    status_aprovado_id = next(s for s in status_relatorio_resp.json() if s['nome'] == 'Aprovado')['id']

    analise_data = {
        "aprovador_usuario_id": admin_user_id,
        "status_id": status_aprovado_id,
        "observacoes_aprovador": "Relatório está completo e aprovado."
    }

    analise_resp = await async_client.patch(
        f"/api/v1/contratos/{contrato_id}/relatorios/{relatorio_id}/analise",
        json=analise_data,
        headers=admin_headers
    )
    assert analise_resp.status_code == 200
    relatorio_aprovado = analise_resp.json()
    assert relatorio_aprovado["status_relatorio"] == "Aprovado"

    # 4. Verificar que a pendência foi marcada como concluída
    pendencias_final = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
    pendencias_list = pendencias_final.json()
    pendencia_atualizada = next(p for p in pendencias_list if p['id'] == pendencia_id)
    assert pendencia_atualizada["status_nome"] == "Concluída"

@pytest.mark.asyncio
async def test_workflow_rejeicao_reenvio(async_client: AsyncClient, admin_headers: Dict, setup_complete_workflow: Dict):
    """Testa o workflow de rejeição e reenvio de relatório."""

    contrato_id = setup_complete_workflow["contrato_id"]
    fiscal_headers = setup_complete_workflow["fiscal_headers"]
    admin_user_id = setup_complete_workflow["admin_user_id"]

    # 1. Criar pendência
    status_pendencia_resp = await async_client.get("/api/v1/statuspendencia/", headers=admin_headers)
    status_pendente_id = next(s for s in status_pendencia_resp.json() if s['nome'] == 'Pendente')['id']

    pendencia_data = {
        "descricao": "Relatório fiscal de fevereiro",
        "data_prazo": str(date(2025, 3, 15)),
        "status_pendencia_id": status_pendente_id,
        "criado_por_usuario_id": admin_user_id
    }

    pendencia_resp = await async_client.post(
        f"/api/v1/contratos/{contrato_id}/pendencias/",
        json=pendencia_data,
        headers=admin_headers
    )
    pendencia = pendencia_resp.json()
    pendencia_id = pendencia["id"]

    # 2. Fiscal submete primeiro relatório
    relatorio_data = {
        "mes_competencia": str(date(2025, 2, 28)),
        "pendencia_id": str(pendencia_id),
        "observacoes_fiscal": "Primeira versão do relatório"
    }
    files = {"arquivo": ("relatorio_v1.pdf", "Conteúdo incompleto", "application/pdf")}

    relatorio_resp = await async_client.post(
        f"/api/v1/contratos/{contrato_id}/relatorios/",
        data=relatorio_data,
        files=files,
        headers=fiscal_headers
    )
    relatorio = relatorio_resp.json()
    relatorio_id = relatorio["id"]

    # 3. Admin rejeita o relatório
    status_relatorio_resp = await async_client.get("/api/v1/statusrelatorio/", headers=admin_headers)
    status_rejeitado_id = next(s for s in status_relatorio_resp.json() if s['nome'] == 'Rejeitado com Pendência')['id']

    rejeicao_data = {
        "aprovador_usuario_id": admin_user_id,
        "status_id": status_rejeitado_id,
        "observacoes_aprovador": "Relatório incompleto. Favor incluir mais detalhes sobre as atividades."
    }

    rejeicao_resp = await async_client.patch(
        f"/api/v1/contratos/{contrato_id}/relatorios/{relatorio_id}/analise",
        json=rejeicao_data,
        headers=admin_headers
    )
    assert rejeicao_resp.status_code == 200
    relatorio_rejeitado = rejeicao_resp.json()
    assert relatorio_rejeitado["status_relatorio"] == "Rejeitado com Pendência"

    # 4. Fiscal reenvia relatório corrigido
    relatorio_corrigido_data = {
        "mes_competencia": str(date(2025, 2, 28)),
        "pendencia_id": str(pendencia_id),
        "observacoes_fiscal": "Relatório corrigido com detalhes adicionais"
    }
    files_corrigido = {"arquivo": ("relatorio_v2_corrigido.pdf", "Conteúdo completo e corrigido", "application/pdf")}

    relatorio_corrigido_resp = await async_client.post(
        f"/api/v1/contratos/{contrato_id}/relatorios/",
        data=relatorio_corrigido_data,
        files=files_corrigido,
        headers=fiscal_headers
    )
    assert relatorio_corrigido_resp.status_code == 201
    relatorio_novo = relatorio_corrigido_resp.json()
    assert relatorio_novo["status_relatorio"] == "Pendente de Análise"

    # O sistema substitui o arquivo anterior (atualiza o relatório existente)
    # Isso está correto pois a documentação indica que reenvios substituem o arquivo anterior
    assert relatorio_novo["id"] == relatorio_id

@pytest.mark.asyncio
async def test_cancelamento_pendencia(async_client: AsyncClient, admin_headers: Dict, setup_complete_workflow: Dict):
    """Testa o cancelamento de pendência pelo administrador."""

    contrato_id = setup_complete_workflow["contrato_id"]
    admin_user_id = setup_complete_workflow["admin_user_id"]

    # 1. Criar pendência
    status_pendencia_resp = await async_client.get("/api/v1/statuspendencia/", headers=admin_headers)
    status_pendente_id = next(s for s in status_pendencia_resp.json() if s['nome'] == 'Pendente')['id']

    pendencia_data = {
        "descricao": "Relatório que será cancelado",
        "data_prazo": str(date(2025, 4, 15)),
        "status_pendencia_id": status_pendente_id,
        "criado_por_usuario_id": admin_user_id
    }

    pendencia_resp = await async_client.post(
        f"/api/v1/contratos/{contrato_id}/pendencias/",
        json=pendencia_data,
        headers=admin_headers
    )
    pendencia = pendencia_resp.json()
    pendencia_id = pendencia["id"]

    # 2. Admin cancela a pendência
    cancelamento_resp = await async_client.patch(
        f"/api/v1/contratos/{contrato_id}/pendencias/{pendencia_id}/cancelar",
        headers=admin_headers
    )
    assert cancelamento_resp.status_code == 200

    # 3. Verificar que foi cancelada
    pendencias_list = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
    pendencias = pendencias_list.json()
    pendencia_cancelada = next(p for p in pendencias if p['id'] == pendencia_id)
    assert pendencia_cancelada["status_nome"] == "Cancelada"

@pytest.mark.asyncio
async def test_listagem_pendencias_contrato(async_client: AsyncClient, admin_headers: Dict, setup_complete_workflow: Dict):
    """Testa a listagem de pendências de um contrato."""

    contrato_id = setup_complete_workflow["contrato_id"]
    admin_user_id = setup_complete_workflow["admin_user_id"]

    # Criar uma pendência de teste
    status_pendencia_resp = await async_client.get("/api/v1/statuspendencia/", headers=admin_headers)
    status_pendente_id = next(s for s in status_pendencia_resp.json() if s['nome'] == 'Pendente')['id']

    pendencia_data = {
        "descricao": "Pendência para teste de listagem",
        "data_prazo": str(date(2025, 6, 15)),
        "status_pendencia_id": status_pendente_id,
        "criado_por_usuario_id": admin_user_id
    }

    await async_client.post(
        f"/api/v1/contratos/{contrato_id}/pendencias/",
        json=pendencia_data,
        headers=admin_headers
    )

    # Listar pendências
    pendencias_resp = await async_client.get(
        f"/api/v1/contratos/{contrato_id}/pendencias/",
        headers=admin_headers
    )
    assert pendencias_resp.status_code == 200
    pendencias = pendencias_resp.json()

    # Verificar estrutura da resposta
    assert isinstance(pendencias, list)
    assert len(pendencias) > 0

    # Verificar estrutura de uma pendência
    pendencia = pendencias[0]
    assert "id" in pendencia
    assert "descricao" in pendencia
    assert "data_prazo" in pendencia
    assert "status_nome" in pendencia
    assert "criado_por_nome" in pendencia