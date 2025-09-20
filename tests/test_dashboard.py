# tests/test_dashboard.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict
import dotenv
import os

dotenv.load_dotenv()

@pytest_asyncio.fixture(scope="function")
def admin_user_data() -> Dict:
    return {"username": os.getenv("ADMIN_EMAIL"), "password": os.getenv("ADMIN_PASSWORD")}

@pytest_asyncio.fixture(scope="function")
async def admin_token(async_client: AsyncClient, admin_user_data: Dict) -> str:
    """Obtém token de administrador para usar nos testes."""
    login_response = await async_client.post("/auth/login", data=admin_user_data)
    assert login_response.status_code == 200
    return login_response.json()["access_token"]

@pytest_asyncio.fixture(scope="function")
async def admin_headers(admin_token: str) -> Dict[str, str]:
    """Headers com autenticação de administrador."""
    return {"Authorization": f"Bearer {admin_token}"}


class TestDashboardAdmin:
    """Testes para endpoints de dashboard do administrador."""

    @pytest.mark.asyncio
    async def test_admin_contratos_com_relatorios_pendentes(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa endpoint de contratos com relatórios pendentes."""
        print("\n--- Testando Contratos com Relatórios Pendentes ---")

        response = await async_client.get(
            "/api/v1/dashboard/admin/contratos-com-relatorios-pendentes",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verifica estrutura da resposta
        assert "contratos" in data
        assert "total_contratos" in data
        assert "total_relatorios_pendentes" in data
        assert isinstance(data["contratos"], list)
        assert isinstance(data["total_contratos"], int)
        assert isinstance(data["total_relatorios_pendentes"], int)

        print(f"--> Encontrados {data['total_contratos']} contratos com relatórios pendentes")

    @pytest.mark.asyncio
    async def test_admin_contratos_com_pendencias(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa endpoint de contratos com pendências."""
        print("\n--- Testando Contratos com Pendências ---")

        response = await async_client.get(
            "/api/v1/dashboard/admin/contratos-com-pendencias",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verifica estrutura da resposta
        assert "contratos" in data
        assert "total_contratos" in data
        assert "total_pendencias" in data
        assert isinstance(data["contratos"], list)
        assert isinstance(data["total_contratos"], int)
        assert isinstance(data["total_pendencias"], int)

        print(f"--> Encontrados {data['total_contratos']} contratos com pendências")

    @pytest.mark.asyncio
    async def test_admin_dashboard_completo(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa endpoint de dashboard completo do administrador."""
        print("\n--- Testando Dashboard Completo do Admin ---")

        response = await async_client.get(
            "/api/v1/dashboard/admin/completo",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verifica estrutura da resposta
        assert "contadores" in data
        assert "contratos_com_relatorios_pendentes" in data
        assert "contratos_com_pendencias" in data

        # Verifica contadores
        contadores = data["contadores"]
        assert "relatorios_para_analise" in contadores
        assert "contratos_com_pendencias" in contadores
        assert "usuarios_ativos" in contadores
        assert "contratos_ativos" in contadores

        print(f"--> Contadores: {contadores['relatorios_para_analise']} relatórios, {contadores['contratos_ativos']} contratos")

    @pytest.mark.asyncio
    async def test_admin_pendencias_vencidas(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa endpoint de pendências vencidas detalhado."""
        print("\n--- Testando Pendências Vencidas Detalhadas ---")

        response = await async_client.get(
            "/api/v1/dashboard/admin/pendencias-vencidas",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verifica estrutura da resposta
        assert "pendencias_vencidas" in data
        assert "total_pendencias_vencidas" in data
        assert "contratos_afetados" in data
        assert "pendencias_criticas" in data
        assert "pendencias_altas" in data
        assert "pendencias_medias" in data

        # Verifica tipos
        assert isinstance(data["pendencias_vencidas"], list)
        assert isinstance(data["total_pendencias_vencidas"], int)
        assert isinstance(data["contratos_afetados"], int)

        print(f"--> {data['total_pendencias_vencidas']} pendências vencidas encontradas")
        print(f"--> {data['contratos_afetados']} contratos afetados")
        print(f"--> Críticas: {data['pendencias_criticas']}, Altas: {data['pendencias_altas']}, Médias: {data['pendencias_medias']}")

        # Se há pendências, verifica estrutura de uma
        if data["pendencias_vencidas"]:
            pendencia = data["pendencias_vencidas"][0]
            campos_obrigatorios = [
                "pendencia_id", "titulo", "descricao", "data_criacao", "prazo_entrega",
                "dias_em_atraso", "contrato_id", "contrato_numero", "contrato_objeto",
                "fiscal_nome", "gestor_nome", "urgencia"
            ]

            for campo in campos_obrigatorios:
                assert campo in pendencia
                assert pendencia[campo] is not None

            # Verifica se urgência é uma das opções válidas
            assert pendencia["urgencia"] in ["CRÍTICA", "ALTA", "MÉDIA"]

            # Verifica se dias_em_atraso é positivo (está realmente vencida)
            assert pendencia["dias_em_atraso"] > 0

    @pytest.mark.asyncio
    async def test_admin_contratos_pendentes_com_limite(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa endpoint com parâmetro de limite."""
        print("\n--- Testando Limite de Resultados ---")

        response = await async_client.get(
            "/api/v1/dashboard/admin/contratos-com-pendencias?limit=5",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verifica que não retorna mais que o limite
        assert len(data["contratos"]) <= 5
        print(f"--> Limitado a 5 resultados: {len(data['contratos'])} contratos retornados")


class TestDashboardFiscal:
    """Testes para endpoints de dashboard do fiscal."""

    @pytest.mark.asyncio
    async def test_fiscal_minhas_pendencias_sem_perfil(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa que admin sem perfil fiscal não pode acessar pendências de fiscal."""
        print("\n--- Testando Acesso Negado para Pendências de Fiscal ---")

        response = await async_client.get(
            "/api/v1/dashboard/fiscal/minhas-pendencias",
            headers=admin_headers
        )

        # Admin puro não tem perfil de fiscal, deve dar 403
        assert response.status_code == 403
        data = response.json()
        assert "fiscal" in data["detail"].lower()
        print("--> Acesso negado corretamente para admin sem perfil fiscal")

    @pytest.mark.asyncio
    async def test_fiscal_dashboard_completo_sem_perfil(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa que admin sem perfil fiscal não pode acessar dashboard fiscal."""
        print("\n--- Testando Dashboard Fiscal sem Perfil ---")

        response = await async_client.get(
            "/api/v1/dashboard/fiscal/completo",
            headers=admin_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert "fiscal" in data["detail"].lower()
        print("--> Dashboard fiscal protegido corretamente")


class TestDashboardGeral:
    """Testes para endpoints gerais de dashboard."""

    @pytest.mark.asyncio
    async def test_contadores_dashboard(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa endpoint de contadores baseado no perfil."""
        print("\n--- Testando Contadores do Dashboard ---")

        response = await async_client.get(
            "/api/v1/dashboard/contadores",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verifica todos os campos de contadores
        campos_esperados = [
            "relatorios_para_analise",
            "contratos_com_pendencias",
            "usuarios_ativos",
            "contratos_ativos",
            "minhas_pendencias",
            "pendencias_em_atraso",
            "relatorios_enviados_mes",
            "contratos_sob_gestao",
            "relatorios_equipe_pendentes"
        ]

        for campo in campos_esperados:
            assert campo in data
            assert isinstance(data[campo], int)
            assert data[campo] >= 0  # Contadores não podem ser negativos

        print(f"--> Contadores obtidos: {data['relatorios_para_analise']} relatórios, {data['usuarios_ativos']} usuários")

    @pytest.mark.asyncio
    async def test_resumo_atividades(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa endpoint de resumo de atividades."""
        print("\n--- Testando Resumo de Atividades ---")

        response = await async_client.get(
            "/api/v1/dashboard/resumo-atividades",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verifica estrutura básica
        assert "perfil" in data
        assert "acao_necessaria" in data
        assert isinstance(data["acao_necessaria"], bool)

        # Para admin, deve ter campos específicos
        if data["perfil"] == "Administrador":
            assert "relatorios_para_analisar" in data
            assert "contratos_com_pendencias" in data

        print(f"--> Perfil: {data['perfil']}, Ação necessária: {data['acao_necessaria']}")

    @pytest.mark.asyncio
    async def test_dashboard_sem_autenticacao(self, async_client: AsyncClient):
        """Testa que endpoints requerem autenticação."""
        print("\n--- Testando Proteção de Autenticação ---")

        endpoints = [
            "/api/v1/dashboard/contadores",
            "/api/v1/dashboard/resumo-atividades",
            "/api/v1/dashboard/admin/contratos-com-pendencias",
            "/api/v1/dashboard/admin/pendencias-vencidas"
        ]

        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            assert response.status_code == 401

        print("--> Todos os endpoints protegidos por autenticação")


class TestDashboardValidacoes:
    """Testes para validações e casos especiais."""

    @pytest.mark.asyncio
    async def test_limite_invalido(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa validação de parâmetro limite."""
        print("\n--- Testando Validação de Limite ---")

        # Teste com limite muito alto
        response = await async_client.get(
            "/api/v1/dashboard/admin/contratos-com-pendencias?limit=200",
            headers=admin_headers
        )
        assert response.status_code == 422  # Validation error

        # Teste com limite zero
        response = await async_client.get(
            "/api/v1/dashboard/admin/contratos-com-pendencias?limit=0",
            headers=admin_headers
        )
        assert response.status_code == 422  # Validation error

        print("--> Validações de limite funcionando corretamente")

    @pytest.mark.asyncio
    async def test_estrutura_resposta_contratos(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa estrutura detalhada das respostas de contratos."""
        print("\n--- Testando Estrutura de Contratos ---")

        response = await async_client.get(
            "/api/v1/dashboard/admin/contratos-com-pendencias?limit=1",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        if data["contratos"]:  # Se há contratos
            contrato = data["contratos"][0]
            campos_obrigatorios = [
                "id", "nr_contrato", "objeto", "data_inicio", "data_fim",
                "contratado_nome", "gestor_nome", "fiscal_nome", "status_nome"
            ]

            for campo in campos_obrigatorios:
                assert campo in contrato
                assert contrato[campo] is not None

        print("--> Estrutura de contratos validada")

    @pytest.mark.asyncio
    async def test_performance_endpoints(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Testa que endpoints respondem em tempo razoável."""
        print("\n--- Testando Performance ---")

        import time

        endpoints = [
            "/api/v1/dashboard/contadores",
            "/api/v1/dashboard/admin/contratos-com-pendencias?limit=10",
            "/api/v1/dashboard/resumo-atividades"
        ]

        for endpoint in endpoints:
            start = time.time()
            response = await async_client.get(endpoint, headers=admin_headers)
            duration = time.time() - start

            assert response.status_code == 200
            assert duration < 5.0  # Deve responder em menos de 5 segundos

            print(f"--> {endpoint}: {duration:.2f}s")


if __name__ == "__main__":
    print("Execute com: pytest tests/test_dashboard.py -v")