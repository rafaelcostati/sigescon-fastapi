"""
Testes para o Middleware de Auditoria
Cobertura: Logs críticos, rastreamento de ações, performance
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
import time
from typing import Dict
import asyncio

from app.middleware.audit import AuditMiddleware
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


class TestAuditMiddleware:
    """Testes para o middleware de auditoria"""

    @pytest_asyncio.fixture
    async def audit_app(self):
        """Cria uma aplicação de teste com middleware de auditoria"""

        async def test_endpoint(request):
            return JSONResponse({"message": "test"})

        async def slow_endpoint(request):
            await asyncio.sleep(0.1)  # Simula operação lenta
            return JSONResponse({"message": "slow"})

        async def error_endpoint(request):
            raise ValueError("Test error")

        routes = [
            Route("/test", test_endpoint),
            Route("/slow", slow_endpoint),
            Route("/error", error_endpoint),
        ]

        app = Starlette(routes=routes)
        app.add_middleware(AuditMiddleware)

        return app

    @pytest.mark.asyncio
    async def test_audit_successful_request(self, audit_app):
        """Testa auditoria de requisição bem-sucedida"""

        with patch('app.middleware.audit.logger') as mock_logger:
            async with AsyncClient(app=audit_app, base_url="http://test") as client:
                response = await client.get("/test")

                assert response.status_code == 200

                # Verifica se o log de auditoria foi chamado
                mock_logger.warning.assert_called()

                # Verifica o conteúdo do log
                log_call = mock_logger.warning.call_args[0][0]
                log_data = json.loads(log_call.split("CRITICAL_ACTION: ")[1])

                assert log_data["method"] == "GET"
                assert log_data["path"] == "/test"
                assert log_data["status_code"] == 200
                assert "process_time" in log_data
                assert "timestamp" in log_data

    @pytest.mark.asyncio
    async def test_audit_slow_request(self, audit_app):
        """Testa auditoria de requisição lenta"""

        with patch('app.middleware.audit.logger') as mock_logger:
            async with AsyncClient(app=audit_app, base_url="http://test") as client:
                start_time = time.time()
                response = await client.get("/slow")
                end_time = time.time()

                assert response.status_code == 200

                # Verifica log
                log_call = mock_logger.warning.call_args[0][0]
                log_data = json.loads(log_call.split("CRITICAL_ACTION: ")[1])

                # Verifica que o tempo foi medido corretamente
                assert log_data["process_time"] >= 0.1
                assert log_data["process_time"] <= (end_time - start_time) + 0.01

    @pytest.mark.asyncio
    async def test_audit_error_request(self, audit_app):
        """Testa auditoria de requisição com erro"""

        with patch('app.middleware.audit.logger') as mock_logger:
            async with AsyncClient(app=audit_app, base_url="http://test") as client:
                response = await client.get("/error")

                assert response.status_code == 500

                # Verifica log de erro
                mock_logger.warning.assert_called()

                log_call = mock_logger.warning.call_args[0][0]
                log_data = json.loads(log_call.split("CRITICAL_ACTION: ")[1])

                assert log_data["status_code"] == 500
                assert log_data["path"] == "/error"

    @pytest.mark.asyncio
    async def test_audit_with_user_context(self, async_client: AsyncClient, admin_headers: Dict):
        """Testa auditoria com contexto de usuário autenticado"""

        with patch('app.middleware.audit.logger') as mock_logger:
            response = await async_client.get("/api/v1/usuarios/me", headers=admin_headers)

            assert response.status_code == 200

            # Verifica se o usuário foi logado
            mock_logger.warning.assert_called()

            log_call = mock_logger.warning.call_args[0][0]
            log_data = json.loads(log_call.split("CRITICAL_ACTION: ")[1])

            assert "user" in log_data
            # Pode ser um ID de usuário ou email, dependendo da implementação

    @pytest.mark.asyncio
    async def test_audit_performance_impact(self, audit_app):
        """Testa impacto de performance do middleware"""

        # Teste sem middleware
        async def simple_endpoint(request):
            return JSONResponse({"message": "test"})

        simple_app = Starlette(routes=[Route("/simple", simple_endpoint)])

        # Mede tempo sem middleware
        async with AsyncClient(app=simple_app, base_url="http://test") as client:
            start = time.time()
            for _ in range(10):
                await client.get("/simple")
            time_without_middleware = time.time() - start

        # Mede tempo com middleware
        async with AsyncClient(app=audit_app, base_url="http://test") as client:
            start = time.time()
            for _ in range(10):
                await client.get("/test")
            time_with_middleware = time.time() - start

        # O overhead do middleware deve ser mínimo (< 50% do tempo base)
        overhead = (time_with_middleware - time_without_middleware) / time_without_middleware
        assert overhead < 0.5, f"Middleware overhead muito alto: {overhead:.2%}"

    @pytest.mark.asyncio
    async def test_audit_concurrent_requests(self, audit_app):
        """Testa auditoria com requisições concorrentes"""

        with patch('app.middleware.audit.logger') as mock_logger:
            async with AsyncClient(app=audit_app, base_url="http://test") as client:
                # Executa 5 requisições concorrentes
                tasks = [client.get("/test") for _ in range(5)]
                responses = await asyncio.gather(*tasks)

                # Todas devem ter sucesso
                for response in responses:
                    assert response.status_code == 200

                # Deve ter 5 logs de auditoria
                assert mock_logger.warning.call_count == 5

    @pytest.mark.asyncio
    async def test_audit_sensitive_data_filtering(self, async_client: AsyncClient):
        """Testa se dados sensíveis são filtrados dos logs"""

        with patch('app.middleware.audit.logger') as mock_logger:
            # Testa login (contém senha)
            login_data = {
                "username": "admin@test.com",
                "password": "secret123"
            }

            response = await async_client.post("/auth/login", data=login_data)

            # Verifica que a senha não aparece no log
            if mock_logger.warning.called:
                log_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
                for log_call in log_calls:
                    assert "secret123" not in log_call
                    assert "password" not in log_call.lower() or "***" in log_call

    @pytest.mark.asyncio
    async def test_audit_different_http_methods(self, async_client: AsyncClient, admin_headers: Dict):
        """Testa auditoria para diferentes métodos HTTP"""

        with patch('app.middleware.audit.logger') as mock_logger:
            # GET
            await async_client.get("/api/v1/usuarios/", headers=admin_headers)

            # POST
            new_user = {
                "nome": "Test User",
                "email": "test@audit.com",
                "cpf": "12345678901",
                "senha": "password123"
            }
            await async_client.post("/api/v1/usuarios/", json=new_user, headers=admin_headers)

            # Verifica logs para ambos os métodos
            assert mock_logger.warning.call_count >= 2

            log_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            methods = []

            for log_call in log_calls:
                if "CRITICAL_ACTION:" in log_call:
                    log_data = json.loads(log_call.split("CRITICAL_ACTION: ")[1])
                    methods.append(log_data["method"])

            assert "GET" in methods
            assert "POST" in methods

    @pytest.mark.asyncio
    async def test_audit_ip_tracking(self, audit_app):
        """Testa rastreamento de IP do cliente"""

        with patch('app.middleware.audit.logger') as mock_logger:
            async with AsyncClient(app=audit_app, base_url="http://test") as client:
                # Adiciona header de IP customizado
                headers = {"X-Forwarded-For": "192.168.1.100"}
                response = await client.get("/test", headers=headers)

                assert response.status_code == 200

                log_call = mock_logger.warning.call_args[0][0]
                log_data = json.loads(log_call.split("CRITICAL_ACTION: ")[1])

                assert "client_ip" in log_data
                # O IP pode ser 127.0.0.1 ou o forwarded IP dependendo da implementação

    def test_audit_log_format_validation(self):
        """Testa se o formato dos logs está correto"""

        # Mock de uma requisição
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client.host = "127.0.0.1"

        # Simula o processamento do middleware
        with patch('app.middleware.audit.logger') as mock_logger:
            with patch('time.time', return_value=1234567890.123):
                # Aqui você precisaria chamar o método específico do middleware
                # que formata o log. Como não temos acesso direto, vamos verificar
                # o formato esperado através de um teste de integração
                pass

        # Verifica que o formato inclui todos os campos obrigatórios
        expected_fields = [
            "timestamp", "method", "path", "status_code",
            "client_ip", "user", "process_time"
        ]

        # Este teste será completado quando tivermos acesso ao método de formatação


@pytest.mark.asyncio
class TestAuditMiddlewareIntegration:
    """Testes de integração do middleware de auditoria"""

    async def test_audit_full_user_workflow(self, async_client: AsyncClient, admin_headers: Dict):
        """Testa auditoria de um fluxo completo de usuário"""

        with patch('app.middleware.audit.logger') as mock_logger:
            # 1. Login (já autenticado via fixture)
            # 2. Listar usuários
            await async_client.get("/api/v1/usuarios/", headers=admin_headers)

            # 3. Criar usuário
            new_user = {
                "nome": "Audit Test User",
                "email": "audit@test.com",
                "cpf": "12345678901",
                "senha": "password123"
            }
            response = await async_client.post("/api/v1/usuarios/", json=new_user, headers=admin_headers)
            user_id = response.json()["id"]

            # 4. Atualizar usuário
            update_data = {"nome": "Updated Audit User"}
            await async_client.patch(f"/api/v1/usuarios/{user_id}", json=update_data, headers=admin_headers)

            # 5. Deletar usuário
            await async_client.delete(f"/api/v1/usuarios/{user_id}", headers=admin_headers)

            # Verifica que todas as ações foram auditadas
            assert mock_logger.warning.call_count >= 4

            # Verifica que diferentes operações CRUD foram logadas
            log_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            methods = set()

            for log_call in log_calls:
                if "CRITICAL_ACTION:" in log_call:
                    log_data = json.loads(log_call.split("CRITICAL_ACTION: ")[1])
                    methods.add(log_data["method"])

            assert "GET" in methods
            assert "POST" in methods
            assert "PATCH" in methods
            assert "DELETE" in methods

    async def test_audit_error_scenarios(self, async_client: AsyncClient):
        """Testa auditoria em cenários de erro"""

        with patch('app.middleware.audit.logger') as mock_logger:
            # 1. Endpoint inexistente (404)
            await async_client.get("/api/v1/nonexistent")

            # 2. Acesso não autorizado (401)
            await async_client.get("/api/v1/usuarios/")

            # 3. Dados inválidos (422)
            invalid_user = {"nome": "", "email": "invalid-email"}
            await async_client.post("/api/v1/usuarios/", json=invalid_user)

            # Verifica que erros foram auditados
            assert mock_logger.warning.call_count >= 3

            # Verifica códigos de status de erro
            log_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            status_codes = []

            for log_call in log_calls:
                if "CRITICAL_ACTION:" in log_call:
                    log_data = json.loads(log_call.split("CRITICAL_ACTION: ")[1])
                    status_codes.append(log_data["status_code"])

            error_codes = [code for code in status_codes if code >= 400]
            assert len(error_codes) >= 3


if __name__ == "__main__":
    pytest.main([__file__])