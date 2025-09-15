# tests/conftest.py
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
import os

# Importa as configurações para ler o .env
from app.core.config import settings

# Garante que a aplicação use a mesma URL de banco de dados definida no .env
# Não é mais necessário um TEST_DATABASE_URL
if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL não foi definida no seu arquivo .env!")


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Cria um cliente HTTP assíncrono para cada função de teste.
    O lifespan da app (que cria o pool de conexão) será ativado aqui.
    """
    from app.main import app  # Importa a app aqui dentro
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client