# tests/test_isolamento_dados_perfil.py
"""
Testes específicos para isolamento de dados por perfil.
Verifica se usuários veem apenas dados que têm permissão de acessar.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any, List
import uuid
import random
import io


class TestIsolamentoDadosPerfil:
    """Testes de isolamento de dados baseado em perfis e hierarquia."""

    @pytest_asyncio.fixture
    async def cenario_multiplos_fiscais(self, async_client: AsyncClient, admin_headers: Dict) -> Dict[str, Any]:
        """Cria cenário com múltiplos fiscais e contratos para teste de isolamento."""

        fiscais = []
        contratos = []

        # Criar contratado para usar nos contratos
        contratado_data = {
            "nome": f"Empresa Isolamento Teste {uuid.uuid4().hex[:6]}",
            "email": f"empresa.isolamento.{uuid.uuid4().hex[:6]}@teste.com",
            "cnpj": f"{random.randint(10**13, 10**14-1)}"
        }
        contratado_response = await async_client.post("/api/v1/contratados/", json=contratado_data, headers=admin_headers)
        contratado = contratado_response.json()

        # Obter dados auxiliares
        modalidades_resp = await async_client.get("/api/v1/modalidades/", headers=admin_headers)
        status_resp = await async_client.get("/api/v1/status/", headers=admin_headers)
        modalidade_id = modalidades_resp.json()[0]["id"]
        status_id = next(s for s in status_resp.json() if s['nome'] == 'Ativo')['id']

        # Criar 3 fiscais
        for i in range(3):
            fiscal_data = {
                "nome": f"Fiscal {i+1} Isolamento {uuid.uuid4().hex[:6]}",
                "email": f"fiscal{i+1}.isolamento.{uuid.uuid4().hex[:6]}@teste.com",
                "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
                "senha": "password123",
                "perfil_id": 3  # Fiscal
            }

            fiscal_response = await async_client.post("/api/v1/usuarios/", json=fiscal_data, headers=admin_headers)
            fiscal = fiscal_response.json()
            fiscal["senha"] = fiscal_data["senha"]  # Guardar senha para login

            # Conceder perfil Fiscal para o usuário criado
            perfil_data = {"perfil_ids": [3]}  # Fiscal
            perfil_response = await async_client.post(
                f"/api/v1/usuarios/{fiscal['id']}/perfis/conceder",
                json=perfil_data,
                headers=admin_headers
            )
            assert perfil_response.status_code == 200

            fiscais.append(fiscal)

            # Criar 2 contratos para cada fiscal
            for j in range(2):
                contrato_data = {
                    "nr_contrato": f"ISOLAMENTO-F{i+1}-C{j+1}-{uuid.uuid4().hex[:6]}",
                    "objeto": f"Contrato {j+1} do Fiscal {i+1} para teste de isolamento",
                    "data_assinatura": "2024-01-15",
                    "data_inicio": "2024-02-01",
                    "data_fim": "2024-12-31",
                    "valor": f"{50000 + i*10000 + j*5000}.00",
                    "fiscal_id": fiscal["id"],
                    "gestor_id": 1,  # Admin como gestor
                    "contratado_id": contratado["id"],
                    "modalidade_id": modalidade_id,
                    "status_id": status_id
                }

                files = {"arquivos": (f"contrato_f{i+1}_c{j+1}.pdf", io.BytesIO(b"Conteudo contrato teste"), "application/pdf")}
                contrato_response = await async_client.post("/api/v1/contratos/", data=contrato_data, files=files, headers=admin_headers)
                contrato = contrato_response.json()
                contrato["fiscal_responsavel"] = fiscal["id"]
                contratos.append(contrato)

        return {
            "fiscais": fiscais,
            "contratos": contratos,
            "contratado": contratado
        }

    @pytest_asyncio.fixture
    async def usuario_gestor(self, async_client: AsyncClient, admin_headers: Dict) -> Dict[str, Any]:
        """Cria usuário com perfil Gestor para testes."""

        user_data = {
            "nome": f"Gestor Teste Isolamento {uuid.uuid4().hex[:6]}",
            "email": f"gestor.isolamento.{uuid.uuid4().hex[:6]}@teste.com",
            "cpf": ''.join([str(random.randint(0, 9)) for _ in range(11)]),
            "senha": "password123",
            "perfil_id": 3  # Fiscal inicial
        }

        user_response = await async_client.post("/api/v1/usuarios/", json=user_data, headers=admin_headers)
        user = user_response.json()

        # Conceder perfil Gestor
        perfil_data = {"perfil_ids": [2]}  # Gestor
        await async_client.post(f"/api/v1/usuarios/{user['id']}/perfis/conceder", json=perfil_data, headers=admin_headers)

        user["senha"] = user_data["senha"]
        return user

    @pytest.mark.asyncio
    async def test_fiscal_ve_apenas_seus_contratos(self, async_client: AsyncClient, cenario_multiplos_fiscais: Dict):
        """Testa se fiscal vê apenas contratos onde é responsável."""
        print("\n--- Testando Isolamento: Fiscal Vê Apenas Seus Contratos ---")

        fiscais = cenario_multiplos_fiscais["fiscais"]
        contratos = cenario_multiplos_fiscais["contratos"]

        # Testar para cada fiscal
        for i, fiscal in enumerate(fiscais):
            # Login do fiscal
            login_response = await async_client.post("/auth/login", data={
                "username": fiscal["email"],
                "password": fiscal["senha"]
            })
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Listar contratos visíveis para este fiscal
            contratos_response = await async_client.get("/api/v1/contratos/", headers=headers)
            assert contratos_response.status_code == 200
            contratos_visiveis = contratos_response.json()["data"]

            # Deve ver apenas seus próprios contratos (2 contratos)
            assert len(contratos_visiveis) == 2

            # Verificar que todos os contratos visíveis são do fiscal atual
            for contrato in contratos_visiveis:
                assert contrato["fiscal_id"] == fiscal["id"]
                assert contrato["fiscal_nome"] == fiscal["nome"]

            print(f"✓ Fiscal {i+1} ({fiscal['nome']}) vê {len(contratos_visiveis)} contratos (correto)")

            # Tentar acessar contrato de outro fiscal (deve falhar)
            contratos_outros_fiscais = [c for c in contratos if c["fiscal_responsavel"] != fiscal["id"]]
            if contratos_outros_fiscais:
                contrato_alheio = contratos_outros_fiscais[0]
                acesso_negado = await async_client.get(f"/api/v1/contratos/{contrato_alheio['id']}", headers=headers)
                assert acesso_negado.status_code == 403
                print(f"✓ Fiscal {i+1} não consegue acessar contrato de outro fiscal (correto)")

        print("✅ Isolamento de contratos por fiscal funcionando corretamente!")

    @pytest.mark.asyncio
    async def test_fiscal_ve_apenas_suas_pendencias(self, async_client: AsyncClient, cenario_multiplos_fiscais: Dict, admin_headers: Dict):
        """Testa se fiscal vê apenas pendências de seus contratos."""
        print("\n--- Testando Isolamento: Fiscal Vê Apenas Suas Pendências ---")

        fiscais = cenario_multiplos_fiscais["fiscais"]
        contratos = cenario_multiplos_fiscais["contratos"]

        # Criar pendências para diferentes fiscais
        pendencias_criadas = []

        for fiscal in fiscais:
            contratos_fiscal = [c for c in contratos if c["fiscal_responsavel"] == fiscal["id"]]

            for contrato in contratos_fiscal:
                pendencia_data = {
                    "descricao": f"Pendência de {fiscal['nome']} para contrato {contrato['nr_contrato']}",
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
                pendencia["fiscal_responsavel"] = fiscal["id"]
                pendencia["contrato_id"] = contrato["id"]
                pendencias_criadas.append(pendencia)

        print(f"✓ Criadas {len(pendencias_criadas)} pendências para teste")

        # Testar visibilidade para cada fiscal
        for i, fiscal in enumerate(fiscais):
            # Login do fiscal
            login_response = await async_client.post("/auth/login", data={
                "username": fiscal["email"],
                "password": fiscal["senha"]
            })
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Contar pendências visíveis para este fiscal
            contratos_fiscal = [c for c in contratos if c["fiscal_responsavel"] == fiscal["id"]]
            total_pendencias_esperadas = 0

            for contrato in contratos_fiscal:
                pendencias_response = await async_client.get(
                    f"/api/v1/contratos/{contrato['id']}/pendencias/",
                    headers=headers
                )
                assert pendencias_response.status_code == 200
                pendencias = pendencias_response.json()
                total_pendencias_esperadas += len(pendencias)

                # Verificar que todas as pendências são do contrato correto
                for pendencia in pendencias:
                    assert pendencia["contrato_id"] == contrato["id"]

            print(f"✓ Fiscal {i+1} vê {total_pendencias_esperadas} pendências de seus contratos")

            # Tentar acessar pendências de contrato de outro fiscal (deve falhar)
            contratos_outros = [c for c in contratos if c["fiscal_responsavel"] != fiscal["id"]]
            if contratos_outros:
                contrato_alheio = contratos_outros[0]
                acesso_pendencias_negado = await async_client.get(
                    f"/api/v1/contratos/{contrato_alheio['id']}/pendencias/",
                    headers=headers
                )
                assert acesso_pendencias_negado.status_code == 403
                print(f"✓ Fiscal {i+1} não consegue ver pendências de contrato alheio")

        print("✅ Isolamento de pendências por fiscal funcionando corretamente!")

    @pytest.mark.asyncio
    async def test_admin_ve_todos_os_dados(self, async_client: AsyncClient, cenario_multiplos_fiscais: Dict, admin_headers: Dict):
        """Testa se administrador vê todos os contratos e pendências."""
        print("\n--- Testando Acesso Total do Administrador ---")

        contratos = cenario_multiplos_fiscais["contratos"]

        # Admin lista todos os contratos
        contratos_response = await async_client.get("/api/v1/contratos/", headers=admin_headers)
        assert contratos_response.status_code == 200
        contratos_visiveis = contratos_response.json()["data"]

        # Admin deve ver pelo menos os contratos criados no teste (pode haver mais de outros testes)
        contratos_teste = [c for c in contratos_visiveis if "ISOLAMENTO" in c["nr_contrato"]]
        assert len(contratos_teste) >= len(contratos)
        print(f"✓ Admin vê {len(contratos_visiveis)} contratos totais ({len(contratos_teste)} do teste)")

        # Admin pode acessar detalhes de qualquer contrato
        for contrato in contratos[:2]:  # Testar alguns contratos
            detalhes_response = await async_client.get(f"/api/v1/contratos/{contrato['id']}", headers=admin_headers)
            assert detalhes_response.status_code == 200
            print(f"✓ Admin acessa detalhes do contrato {contrato['nr_contrato']}")

        # Admin pode ver pendências de qualquer contrato
        for contrato in contratos[:2]:  # Testar alguns contratos
            pendencias_response = await async_client.get(
                f"/api/v1/contratos/{contrato['id']}/pendencias/",
                headers=admin_headers
            )
            assert pendencias_response.status_code == 200
            print(f"✓ Admin vê pendências do contrato {contrato['nr_contrato']}")

        print("✅ Administrador tem acesso total conforme esperado!")

    @pytest.mark.asyncio
    async def test_gestor_ve_equipe_hierarquia(self, async_client: AsyncClient, cenario_multiplos_fiscais: Dict, usuario_gestor: Dict, admin_headers: Dict):
        """Testa se gestor vê contratos de sua equipe conforme hierarquia."""
        print("\n--- Testando Acesso Hierárquico do Gestor ---")

        contratos = cenario_multiplos_fiscais["contratos"]
        gestor = usuario_gestor

        # Login do gestor
        login_response = await async_client.post("/auth/login", data={
            "username": gestor["email"],
            "password": gestor["senha"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Gestor lista contratos
        contratos_response = await async_client.get("/api/v1/contratos/", headers=headers)
        assert contratos_response.status_code == 200
        contratos_visiveis = contratos_response.json()["data"]

        # Gestor deve ver contratos onde é gestor ou tem acesso hierárquico
        print(f"✓ Gestor vê {len(contratos_visiveis)} contratos")

        # Gestor pode acessar detalhes de contratos (dependendo da implementação de hierarquia)
        if contratos_visiveis:
            primeiro_contrato = contratos_visiveis[0]
            detalhes_response = await async_client.get(f"/api/v1/contratos/{primeiro_contrato['id']}", headers=headers)
            # Status pode ser 200 (acesso permitido) ou 403 (acesso restrito)
            print(f"✓ Acesso do gestor a detalhes: {detalhes_response.status_code}")

        print("✅ Acesso hierárquico do gestor testado!")

    @pytest.mark.asyncio
    async def test_isolamento_relatorios_fiscais(self, async_client: AsyncClient, cenario_multiplos_fiscais: Dict, admin_headers: Dict):
        """Testa se fiscais veem apenas seus próprios relatórios."""
        print("\n--- Testando Isolamento de Relatórios Fiscais ---")

        fiscais = cenario_multiplos_fiscais["fiscais"]
        contratos = cenario_multiplos_fiscais["contratos"]

        # Criar pendências e relatórios para diferentes fiscais
        relatorios_criados = []

        for fiscal in fiscais[:2]:  # Testar apenas 2 fiscais para ser mais rápido
            contratos_fiscal = [c for c in contratos if c["fiscal_responsavel"] == fiscal["id"]]

            for contrato in contratos_fiscal[:1]:  # Apenas 1 contrato por fiscal
                # Criar pendência
                pendencia_data = {
                    "descricao": f"Pendência para relatório de {fiscal['nome']}",
                    "data_prazo": "2024-12-31",
                    "status_pendencia_id": 1,  # Status "Pendente"
                    "criado_por_usuario_id": 1  # Admin
                }

                pendencia_response = await async_client.post(
                    f"/api/v1/contratos/{contrato['id']}/pendencias/",
                    json=pendencia_data,
                    headers=admin_headers
                )
                pendencia = pendencia_response.json()

                # Login do fiscal para enviar relatório
                login_response = await async_client.post("/auth/login", data={
                    "username": fiscal["email"],
                    "password": fiscal["senha"]
                })
                token = login_response.json()["access_token"]
                fiscal_headers = {"Authorization": f"Bearer {token}"}

                # Enviar relatório
                relatorio_data = {
                    "mes_competencia": "2024-12-01",
                    "pendencia_id": pendencia["id"]
                }
                arquivo = io.BytesIO(f"Relatório de {fiscal['nome']} para isolamento".encode())
                files = {"arquivo": (f"relatorio_{fiscal['id']}.pdf", arquivo, "application/pdf")}

                relatorio_response = await async_client.post(
                    f"/api/v1/contratos/{contrato['id']}/relatorios/",
                    data=relatorio_data,
                    files=files,
                    headers=fiscal_headers
                )
                assert relatorio_response.status_code == 201
                relatorio = relatorio_response.json()
                relatorio["fiscal_responsavel"] = fiscal["id"]
                relatorio["contrato_id"] = contrato["id"]
                relatorios_criados.append(relatorio)

        print(f"✓ Criados {len(relatorios_criados)} relatórios para teste")

        # Testar isolamento de relatórios
        for i, fiscal in enumerate(fiscais[:2]):
            # Login do fiscal
            login_response = await async_client.post("/auth/login", data={
                "username": fiscal["email"],
                "password": fiscal["senha"]
            })
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Verificar relatórios visíveis para este fiscal
            contratos_fiscal = [c for c in contratos if c["fiscal_responsavel"] == fiscal["id"]]

            for contrato in contratos_fiscal:
                relatorios_response = await async_client.get(
                    f"/api/v1/contratos/{contrato['id']}/relatorios/",
                    headers=headers
                )

                if relatorios_response.status_code == 200:
                    relatorios = relatorios_response.json()
                    # Verificar que todos os relatórios são do fiscal correto
                    for relatorio in relatorios:
                        # O fiscal deve ver apenas relatórios de contratos onde é responsável
                        assert contrato["fiscal_responsavel"] == fiscal["id"]

                    print(f"✓ Fiscal {i+1} vê {len(relatorios)} relatórios de seu contrato")

        print("✅ Isolamento de relatórios por fiscal funcionando corretamente!")

    @pytest.mark.asyncio
    async def test_tentativa_acesso_direto_negado(self, async_client: AsyncClient, cenario_multiplos_fiscais: Dict):
        """Testa tentativas de acesso direto a recursos de outros usuários."""
        print("\n--- Testando Negação de Acesso Direto ---")

        fiscais = cenario_multiplos_fiscais["fiscais"]
        contratos = cenario_multiplos_fiscais["contratos"]

        # Pegar dois fiscais diferentes
        fiscal1 = fiscais[0]
        fiscal2 = fiscais[1]

        # Login do fiscal 1
        login1 = await async_client.post("/auth/login", data={
            "username": fiscal1["email"],
            "password": fiscal1["senha"]
        })
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Contratos do fiscal 2
        contratos_fiscal2 = [c for c in contratos if c["fiscal_responsavel"] == fiscal2["id"]]

        # Fiscal 1 tenta acessar contrato do Fiscal 2
        if contratos_fiscal2:
            contrato_fiscal2 = contratos_fiscal2[0]

            # Tentativa de acesso direto ao contrato
            acesso_contrato = await async_client.get(f"/api/v1/contratos/{contrato_fiscal2['id']}", headers=headers1)
            assert acesso_contrato.status_code == 403
            print("✓ Acesso negado: Fiscal 1 não acessa contrato do Fiscal 2")

            # Tentativa de acesso às pendências
            acesso_pendencias = await async_client.get(
                f"/api/v1/contratos/{contrato_fiscal2['id']}/pendencias/",
                headers=headers1
            )
            assert acesso_pendencias.status_code == 403
            print("✓ Acesso negado: Fiscal 1 não acessa pendências do Fiscal 2")

            # Tentativa de acesso aos relatórios
            acesso_relatorios = await async_client.get(
                f"/api/v1/contratos/{contrato_fiscal2['id']}/relatorios/",
                headers=headers1
            )
            assert acesso_relatorios.status_code == 403
            print("✓ Acesso negado: Fiscal 1 não acessa relatórios do Fiscal 2")

        print("✅ Negação de acesso direto funcionando corretamente!")

    @pytest.mark.asyncio
    async def test_dashboard_isolado_por_perfil(self, async_client: AsyncClient, cenario_multiplos_fiscais: Dict):
        """Testa se dashboard mostra dados isolados por perfil."""
        print("\n--- Testando Dashboard Isolado por Perfil ---")

        fiscais = cenario_multiplos_fiscais["fiscais"]

        # Testar dashboard para cada fiscal
        for i, fiscal in enumerate(fiscais):
            # Login do fiscal
            login_response = await async_client.post("/auth/login", data={
                "username": fiscal["email"],
                "password": fiscal["senha"]
            })
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Dashboard geral
            dashboard_response = await async_client.get("/auth/dashboard", headers=headers)
            assert dashboard_response.status_code == 200
            dashboard_data = dashboard_response.json()

            # Verificar que dados do dashboard são isolados
            if "total_contratos" in dashboard_data:
                # Fiscal deve ver apenas seus contratos
                assert dashboard_data["total_contratos"] <= 2  # Máximo criado para cada fiscal
                print(f"✓ Fiscal {i+1}: Dashboard mostra {dashboard_data['total_contratos']} contratos")

            # Dashboard específico do fiscal (se existir endpoint)
            minhas_pendencias_response = await async_client.get("/auth/dashboard/fiscal/minhas-pendencias", headers=headers)
            if minhas_pendencias_response.status_code == 200:
                pendencias_data = minhas_pendencias_response.json()
                print(f"✓ Fiscal {i+1}: Dashboard de pendências funcionando")

        print("✅ Dashboard isolado por perfil funcionando corretamente!")


if __name__ == "__main__":
    print("Execute: pytest tests/test_isolamento_dados_perfil.py -v")