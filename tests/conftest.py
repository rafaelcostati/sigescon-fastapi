# tests/conftest.py
import pytest
import asyncpg
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db_pool, close_db_pool
from app.seeder import seed_data
from app.core.config import settings

# Garante que os testes usem um banco de dados separado
# É FUNDAMENTAL ter uma variável de ambiente para o banco de teste no seu .env
# Ex: TEST_DATABASE_URL=postgresql://user:pass@host:port/test_db
settings.DATABASE_URL = "postgresql://rafael:1234@localhost:5432/test_db_contratos"


async def setup_database():
    """Cria o pool, popula a base e retorna o pool."""
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        # Aqui você pode rodar migrations se usar Alembic, etc.
        # Por enquanto, vamos apenas popular
        await seed_data(connection)
    return pool

async def teardown_database(pool):
    """Limpa a base de dados e fecha o pool."""
    async with pool.acquire() as connection:
        # Limpa as tabelas na ordem correta para evitar erros de FK
        await connection.execute("TRUNCATE TABLE contratado, usuario, perfil RESTART IDENTITY CASCADE")
    await close_db_pool()


@pytest.fixture(scope="session", autouse=True)
async def db_setup_session():
    """
    Fixture de sessão para configurar e destruir o banco de dados
    apenas uma vez para toda a sessão de testes.
    """
    pool = await setup_database()
    yield
    await teardown_database(pool)


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Cria um cliente HTTP assíncrono para cada função de teste,
    garantindo isolamento.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client