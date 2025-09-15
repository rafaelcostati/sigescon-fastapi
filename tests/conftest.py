# tests/conftest.py
import pytest
from httpx import AsyncClient
from typing import AsyncGenerator

from app.main import app

@pytest.fixture(scope="module")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Cria um cliente HTTP assíncrono para fazer requisições à nossa API nos testes.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client