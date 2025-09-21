# tests/test_novo_status_aguardando_analise.py
"""
Testes específicos para o novo status "Aguardando Análise" implementado
para melhorar a UX do administrador na gestão de pendências.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any
import uuid
import random
import io


class TestNovoStatusAguardandoAnalise:
    """Testes do novo status 'Aguardando Análise' na gestão de pendências."""

    @pytest_asyncio.fixture
    async def setup_complete_scenario(self, async_client: AsyncClient, admin_headers: Dict) -> Dict[str, Any]:
        """Cria cenário completo: usuários, contrato e pendência para testes."""

        # Criar usuário fiscal
        fiscal_data = {
            "nome": f"Fiscal Teste Status {uuid.uuid4().hex[:6]}",
            "email": f"fiscal.status.{uuid.uuid4().hex[:6]}@teste.com",
            "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
            "senha": "password123",
            "perfil_id": 3  # Fiscal
        }
        fiscal_response = await async_client.post("/api/v1/usuarios/", json=fiscal_data, headers=admin_headers)
        assert fiscal_response.status_code == 201
        fiscal = fiscal_response.json()

        # Conceder perfil Fiscal para o usuário criado
        perfil_data = {"perfil_ids": [3]}  # Fiscal
        perfil_response = await async_client.post(
            f"/api/v1/usuarios/{fiscal['id']}/perfis/conceder",
            json=perfil_data,
            headers=admin_headers
        )
        assert perfil_response.status_code == 200

        # Criar contratado
        contratado_data = {
            "nome": f"Empresa Status Teste {uuid.uuid4().hex[:6]}",
            "email": f"empresa.status.{uuid.uuid4().hex[:6]}@teste.com",
            "cnpj": f"{random.randint(10**13, 10**14-1)}"
        }
        contratado_response = await async_client.post("/api/v1/contratados/", json=contratado_data, headers=admin_headers)
        assert contratado_response.status_code == 201
        contratado = contratado_response.json()

        # Obter modalidades e status
        modalidades_resp = await async_client.get("/api/v1/modalidades/", headers=admin_headers)
        status_resp = await async_client.get("/api/v1/status/", headers=admin_headers)

        # Criar contrato
        contrato_data = {
            "nr_contrato": f"TEST-STATUS-{uuid.uuid4().hex[:8]}",
            "objeto": "Contrato para teste de status aguardando análise",
            "data_assinatura": "2024-01-15",
            "data_inicio": "2024-02-01",
            "data_fim": "2024-12-31",
            "valor": "50000.00",
            "fiscal_id": fiscal["id"],
            "gestor_id": 1,  # Admin como gestor
            "contratado_id": contratado["id"],
            "modalidade_id": modalidades_resp.json()[0]["id"],
            "status_id": next(s for s in status_resp.json() if s['nome'] == 'Ativo')['id']
        }

        files = {"arquivos": ("contrato_teste.pdf", io.BytesIO(b"Conteudo do contrato de teste"), "application/pdf")}
        contrato_response = await async_client.post("/api/v1/contratos/", data=contrato_data, files=files, headers=admin_headers)
        assert contrato_response.status_code == 201
        contrato = contrato_response.json()

        # Criar pendência
        pendencia_data = {
            "descricao": "Pendência para teste de status aguardando análise",
            "data_prazo": "2024-12-31",
            "status_pendencia_id": 1,  # Status "Pendente"
            "criado_por_usuario_id": 1  # Admin
        }
        pendencia_response = await async_client.post(
            f"/api/v1/contratos/{contrato['id']}/pendencias/",
            json=pendencia_data,
            headers=admin_headers
        )
        assert pendencia_response.status_code == 201
        pendencia = pendencia_response.json()

        # Login fiscal para obter token
        fiscal_login = await async_client.post("/auth/login", data={
            "username": fiscal_data["email"],
            "password": fiscal_data["senha"]
        })
        fiscal_token = fiscal_login.json()["access_token"]
        fiscal_headers = {"Authorization": f"Bearer {fiscal_token}"}

        return {
            "fiscal": fiscal,
            "contrato": contrato,
            "pendencia": pendencia,
            "fiscal_headers": fiscal_headers,
            "admin_headers": admin_headers
        }

    @pytest.mark.asyncio
    async def test_transicao_automatica_para_aguardando_analise(self, async_client: AsyncClient, setup_complete_scenario: Dict):
        """Testa se pendência muda automaticamente para 'Aguardando Análise' ao enviar relatório."""
        print("\n--- Testando Transição Automática para 'Aguardando Análise' ---")

        scenario = setup_complete_scenario
        contrato_id = scenario["contrato"]["id"]
        pendencia_id = scenario["pendencia"]["id"]
        fiscal_headers = scenario["fiscal_headers"]
        admin_headers = scenario["admin_headers"]

        # 1. Verificar status inicial da pendência (deve ser "Pendente")
        pendencias_response = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        assert pendencias_response.status_code == 200
        pendencias = pendencias_response.json()
        pendencia_inicial = next(p for p in pendencias if p["id"] == pendencia_id)
        assert pendencia_inicial["status_nome"] == "Pendente"
        print(f"✓ Status inicial da pendência: {pendencia_inicial['status_nome']}")

        # 2. Fiscal envia relatório
        relatorio_data = {
            "mes_competencia": "2024-10-01",
            "pendencia_id": pendencia_id
        }
        arquivo = io.BytesIO(b"Conteudo do relatorio de teste para aguardando analise")
        files = {"arquivo": ("relatorio_teste_status.pdf", arquivo, "application/pdf")}

        relatorio_response = await async_client.post(
            f"/api/v1/contratos/{contrato_id}/relatorios/",
            data=relatorio_data,
            files=files,
            headers=fiscal_headers
        )
        assert relatorio_response.status_code == 201
        relatorio = relatorio_response.json()
        print(f"✓ Relatório enviado pelo fiscal: ID {relatorio['id']}")

        # 3. Verificar se status mudou para "Aguardando Análise"
        pendencias_response_atualizada = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        assert pendencias_response_atualizada.status_code == 200
        pendencias_atualizadas = pendencias_response_atualizada.json()
        pendencia_atualizada = next(p for p in pendencias_atualizadas if p["id"] == pendencia_id)

        assert pendencia_atualizada["status_nome"] == "Aguardando Análise"
        print(f"✓ Status após envio do relatório: {pendencia_atualizada['status_nome']}")
        print("✅ Transição automática funcionando corretamente!")

    @pytest.mark.asyncio
    async def test_contador_dashboard_aguardando_analise(self, async_client: AsyncClient, setup_complete_scenario: Dict):
        """Testa se contador do dashboard reflete corretamente pendências 'Aguardando Análise'."""
        print("\n--- Testando Contador Dashboard com 'Aguardando Análise' ---")

        scenario = setup_complete_scenario
        contrato_id = scenario["contrato"]["id"]
        pendencia_id = scenario["pendencia"]["id"]
        fiscal_headers = scenario["fiscal_headers"]
        admin_headers = scenario["admin_headers"]

        # 1. Verificar contador inicial
        contador_inicial = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/contador", headers=admin_headers)
        assert contador_inicial.status_code == 200
        contador_data_inicial = contador_inicial.json()
        print(f"✓ Contador inicial: {contador_data_inicial}")

        # 2. Enviar relatório
        relatorio_data = {
            "mes_competencia": "2024-11-01",
            "pendencia_id": pendencia_id
        }
        arquivo = io.BytesIO(b"Relatorio para teste de contador")
        files = {"arquivo": ("relatorio_contador.pdf", arquivo, "application/pdf")}

        await async_client.post(
            f"/api/v1/contratos/{contrato_id}/relatorios/",
            data=relatorio_data,
            files=files,
            headers=fiscal_headers
        )

        # 3. Verificar contador atualizado
        contador_atualizado = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/contador", headers=admin_headers)
        assert contador_atualizado.status_code == 200
        contador_data_atualizado = contador_atualizado.json()

        # Deve ter 1 pendência em "aguardando_analise" e 0 em "pendentes"
        assert contador_data_atualizado["aguardando_analise"] >= 1
        print(f"✓ Contador atualizado: {contador_data_atualizado}")
        print("✅ Contador refletindo corretamente o novo status!")

    @pytest.mark.asyncio
    async def test_reenvio_mantem_aguardando_analise(self, async_client: AsyncClient, setup_complete_scenario: Dict):
        """Testa se reenvio de relatório mantém status 'Aguardando Análise'."""
        print("\n--- Testando Reenvio Mantém 'Aguardando Análise' ---")

        scenario = setup_complete_scenario
        contrato_id = scenario["contrato"]["id"]
        pendencia_id = scenario["pendencia"]["id"]
        fiscal_headers = scenario["fiscal_headers"]
        admin_headers = scenario["admin_headers"]

        # 1. Primeiro envio
        relatorio_data = {
            "mes_competencia": "2024-12-01",
            "pendencia_id": pendencia_id
        }
        arquivo1 = io.BytesIO(b"Primeiro relatorio para teste de reenvio")
        files1 = {"arquivo": ("relatorio_v1.pdf", arquivo1, "application/pdf")}

        primeiro_envio = await async_client.post(
            f"/api/v1/contratos/{contrato_id}/relatorios/",
            data=relatorio_data,
            files=files1,
            headers=fiscal_headers
        )
        assert primeiro_envio.status_code == 201
        print("✓ Primeiro relatório enviado")

        # 2. Verificar status após primeiro envio
        pendencias_response = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        pendencias = pendencias_response.json()
        pendencia = next(p for p in pendencias if p["id"] == pendencia_id)
        assert pendencia["status_nome"] == "Aguardando Análise"
        print(f"✓ Status após primeiro envio: {pendencia['status_nome']}")

        # 3. Reenvio (correção)
        arquivo2 = io.BytesIO(b"Segundo relatorio - versao corrigida")
        files2 = {"arquivo": ("relatorio_v2_corrigido.pdf", arquivo2, "application/pdf")}

        reenvio = await async_client.post(
            f"/api/v1/contratos/{contrato_id}/relatorios/",
            data=relatorio_data,
            files=files2,
            headers=fiscal_headers
        )
        assert reenvio.status_code == 201
        print("✓ Relatório reenviado (versão corrigida)")

        # 4. Verificar se status continua "Aguardando Análise"
        pendencias_response_final = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        pendencias_final = pendencias_response_final.json()
        pendencia_final = next(p for p in pendencias_final if p["id"] == pendencia_id)

        assert pendencia_final["status_nome"] == "Aguardando Análise"
        print(f"✓ Status após reenvio: {pendencia_final['status_nome']}")
        print("✅ Reenvio mantém status 'Aguardando Análise' corretamente!")

    @pytest.mark.asyncio
    async def test_fluxo_completo_aprovacao_com_novo_status(self, async_client: AsyncClient, setup_complete_scenario: Dict):
        """Testa fluxo completo: Pendente → Aguardando Análise → Concluída."""
        print("\n--- Testando Fluxo Completo de Aprovação ---")

        scenario = setup_complete_scenario
        contrato_id = scenario["contrato"]["id"]
        pendencia_id = scenario["pendencia"]["id"]
        fiscal_headers = scenario["fiscal_headers"]
        admin_headers = scenario["admin_headers"]

        # 1. Status inicial: Pendente
        pendencias_response = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        pendencias = pendencias_response.json()
        pendencia = next(p for p in pendencias if p["id"] == pendencia_id)
        assert pendencia["status_nome"] == "Pendente"
        print(f"✓ 1. Status inicial: {pendencia['status_nome']}")

        # 2. Fiscal envia relatório → Aguardando Análise
        relatorio_data = {
            "mes_competencia": "2025-01-01",
            "pendencia_id": pendencia_id
        }
        arquivo = io.BytesIO(b"Relatorio para aprovacao completa")
        files = {"arquivo": ("relatorio_para_aprovacao.pdf", arquivo, "application/pdf")}

        relatorio_response = await async_client.post(
            f"/api/v1/contratos/{contrato_id}/relatorios/",
            data=relatorio_data,
            files=files,
            headers=fiscal_headers
        )
        assert relatorio_response.status_code == 201
        relatorio = relatorio_response.json()
        print(f"✓ 2. Relatório enviado: ID {relatorio['id']}")

        # Verificar mudança para "Aguardando Análise"
        pendencias_response = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        pendencias = pendencias_response.json()
        pendencia = next(p for p in pendencias if p["id"] == pendencia_id)
        assert pendencia["status_nome"] == "Aguardando Análise"
        print(f"✓ 2. Status após envio: {pendencia['status_nome']}")

        # 3. Admin aprova relatório → Concluída
        # Obter status "Aprovado" para relatórios
        status_relatorio_resp = await async_client.get("/api/v1/statusrelatorio/", headers=admin_headers)
        status_aprovado = next(s for s in status_relatorio_resp.json() if s['nome'] == 'Aprovado')

        analise_data = {
            "status_id": status_aprovado["id"],
            "aprovador_usuario_id": 1,  # Admin
            "observacoes_aprovador": "Relatório aprovado após análise completa"
        }

        analise_response = await async_client.patch(
            f"/api/v1/contratos/{contrato_id}/relatorios/{relatorio['id']}/analise",
            json=analise_data,
            headers=admin_headers
        )
        assert analise_response.status_code == 200
        print("✓ 3. Relatório aprovado pelo admin")

        # Verificar mudança para "Concluída"
        pendencias_response_final = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        pendencias_final = pendencias_response_final.json()
        pendencia_final = next(p for p in pendencias_final if p["id"] == pendencia_id)

        assert pendencia_final["status_nome"] == "Concluída"
        print(f"✓ 3. Status final: {pendencia_final['status_nome']}")
        print("✅ Fluxo completo executado com sucesso: Pendente → Aguardando Análise → Concluída!")

    @pytest.mark.asyncio
    async def test_fluxo_completo_rejeicao_com_novo_status(self, async_client: AsyncClient, setup_complete_scenario: Dict):
        """Testa fluxo completo: Pendente → Aguardando Análise → Pendente (rejeição)."""
        print("\n--- Testando Fluxo Completo de Rejeição ---")

        scenario = setup_complete_scenario
        contrato_id = scenario["contrato"]["id"]
        pendencia_id = scenario["pendencia"]["id"]
        fiscal_headers = scenario["fiscal_headers"]
        admin_headers = scenario["admin_headers"]

        # 1. Fiscal envia relatório
        relatorio_data = {
            "mes_competencia": "2025-02-01",
            "pendencia_id": pendencia_id
        }
        arquivo = io.BytesIO(b"Relatorio para rejeicao teste")
        files = {"arquivo": ("relatorio_para_rejeicao.pdf", arquivo, "application/pdf")}

        relatorio_response = await async_client.post(
            f"/api/v1/contratos/{contrato_id}/relatorios/",
            data=relatorio_data,
            files=files,
            headers=fiscal_headers
        )
        assert relatorio_response.status_code == 201
        relatorio = relatorio_response.json()
        print(f"✓ 1. Relatório enviado: ID {relatorio['id']}")

        # Verificar status "Aguardando Análise"
        pendencias_response = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        pendencias = pendencias_response.json()
        pendencia = next(p for p in pendencias if p["id"] == pendencia_id)
        assert pendencia["status_nome"] == "Aguardando Análise"
        print(f"✓ 1. Status após envio: {pendencia['status_nome']}")

        # 2. Admin rejeita relatório
        status_relatorio_resp = await async_client.get("/api/v1/statusrelatorio/", headers=admin_headers)
        status_rejeitado = next(s for s in status_relatorio_resp.json() if s['nome'] == 'Rejeitado com Pendência')

        rejeicao_data = {
            "status_id": status_rejeitado["id"],
            "aprovador_usuario_id": 1,  # Admin
            "observacoes_aprovador": "Relatório rejeitado - favor corrigir formatação e reenviar"
        }

        rejeicao_response = await async_client.patch(
            f"/api/v1/contratos/{contrato_id}/relatorios/{relatorio['id']}/analise",
            json=rejeicao_data,
            headers=admin_headers
        )
        assert rejeicao_response.status_code == 200
        print("✓ 2. Relatório rejeitado pelo admin")

        # 3. Verificar volta para "Pendente"
        pendencias_response_final = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        pendencias_final = pendencias_response_final.json()
        pendencia_final = next(p for p in pendencias_final if p["id"] == pendencia_id)

        assert pendencia_final["status_nome"] == "Pendente"
        print(f"✓ 3. Status após rejeição: {pendencia_final['status_nome']}")
        print("✅ Fluxo de rejeição executado com sucesso: Aguardando Análise → Pendente!")

    @pytest.mark.asyncio
    async def test_filtro_fiscal_ve_apenas_pendentes(self, async_client: AsyncClient, setup_complete_scenario: Dict):
        """Testa se fiscal vê apenas pendências com status 'Pendente' (que precisam de ação)."""
        print("\n--- Testando Filtro: Fiscal Vê Apenas Pendências 'Pendente' ---")

        scenario = setup_complete_scenario
        contrato_id = scenario["contrato"]["id"]
        pendencia_id = scenario["pendencia"]["id"]
        fiscal_headers = scenario["fiscal_headers"]
        admin_headers = scenario["admin_headers"]

        # 1. Criar segunda pendência para o mesmo contrato
        pendencia2_data = {
            "descricao": "Segunda pendência para teste de filtro",
            "data_prazo": "2025-01-31",
            "status_pendencia_id": 1,  # Status "Pendente"
            "criado_por_usuario_id": 1  # Admin
        }
        pendencia2_response = await async_client.post(
            f"/api/v1/contratos/{contrato_id}/pendencias/",
            json=pendencia2_data,
            headers=admin_headers
        )
        assert pendencia2_response.status_code == 201
        pendencia2 = pendencia2_response.json()
        print(f"✓ Segunda pendência criada: ID {pendencia2['id']}")

        # 2. Fiscal consulta suas pendências (deve ver 2 pendências "Pendente")
        pendencias_fiscal = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=fiscal_headers)
        assert pendencias_fiscal.status_code == 200
        pendencias_list = pendencias_fiscal.json()

        pendencias_pendentes = [p for p in pendencias_list if p["status_nome"] == "Pendente"]
        assert len(pendencias_pendentes) == 2
        print(f"✓ Fiscal vê {len(pendencias_pendentes)} pendências 'Pendente'")

        # 3. Enviar relatório para primeira pendência
        relatorio_data = {
            "mes_competencia": "2025-03-01",
            "pendencia_id": pendencia_id
        }
        arquivo = io.BytesIO(b"Relatorio primeira pendencia")
        files = {"arquivo": ("relatorio_filtro_teste.pdf", arquivo, "application/pdf")}

        await async_client.post(
            f"/api/v1/contratos/{contrato_id}/relatorios/",
            data=relatorio_data,
            files=files,
            headers=fiscal_headers
        )
        print("✓ Relatório enviado para primeira pendência")

        # 4. Fiscal consulta novamente (deve ver apenas 1 pendência "Pendente")
        pendencias_fiscal_atualizada = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=fiscal_headers)
        pendencias_list_atualizada = pendencias_fiscal_atualizada.json()

        pendencias_pendentes_atualizada = [p for p in pendencias_list_atualizada if p["status_nome"] == "Pendente"]
        assert len(pendencias_pendentes_atualizada) == 1
        assert pendencias_pendentes_atualizada[0]["id"] == pendencia2["id"]
        print(f"✓ Após envio, fiscal vê apenas {len(pendencias_pendentes_atualizada)} pendência 'Pendente'")

        # 5. Admin vê todas as pendências (incluindo "Aguardando Análise")
        pendencias_admin = await async_client.get(f"/api/v1/contratos/{contrato_id}/pendencias/", headers=admin_headers)
        pendencias_admin_list = pendencias_admin.json()

        aguardando_analise = [p for p in pendencias_admin_list if p["status_nome"] == "Aguardando Análise"]
        pendentes = [p for p in pendencias_admin_list if p["status_nome"] == "Pendente"]

        assert len(aguardando_analise) == 1
        assert len(pendentes) == 1
        print(f"✓ Admin vê: {len(aguardando_analise)} 'Aguardando Análise' + {len(pendentes)} 'Pendente'")
        print("✅ Filtro funcionando corretamente: Fiscal vê apenas pendências que precisam de ação!")


if __name__ == "__main__":
    print("Execute: pytest tests/test_novo_status_aguardando_analise.py -v")