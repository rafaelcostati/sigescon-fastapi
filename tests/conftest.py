# tests/conftest.py 
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
import asyncpg
import os

# Adiciona o diretório raiz do projeto ao path do Python
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import get_db_pool, close_db_pool
from app.seeder import seed_data

# Garante que a aplicação use a mesma URL de banco de dados definida no .env
if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL não foi definida no seu arquivo .env!")

@pytest_asyncio.fixture(scope="session")
async def setup_test_database():
    """
    Configura o banco de dados para os testes da sessão inteira.
    Executa o seeder para garantir que os dados necessários existam.
    """
    # Cria uma conexão direta para o seeder
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        await seed_data(conn)
        print("Dados de teste populados no banco.")
    finally:
        await conn.close()
    
    yield
    
    # Opcional: limpar dados específicos de teste após a sessão
    print("Limpeza após testes concluída.")

@pytest_asyncio.fixture(scope="function")
async def async_client(setup_test_database) -> AsyncGenerator[AsyncClient, None]:
    """
    Cria um cliente HTTP assíncrono para cada função de teste.
    O lifespan da app (que cria o pool de conexão) será ativado aqui.
    """
    from app.main import app  # Importa a app aqui dentro
    
    # Garante que o pool do banco está limpo antes de cada teste
    await close_db_pool()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Limpa o pool após cada teste para evitar problemas de conexão
    await close_db_pool()

# Fixture adicional para testes que precisam de conexão direta com o banco
@pytest_asyncio.fixture(scope="function")
async def db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Fornece uma conexão direta com o banco para testes que precisam.
    """
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()
        
# Fixtures de autenticação
@pytest_asyncio.fixture(scope="function")
async def admin_credentials():
    """Credenciais do administrador"""
    from dotenv import load_dotenv
    load_dotenv()  # Garantir que .env é carregado
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        # Fallback para valores padrão se env não estiver carregado
        email = "admin@sigescon.pge.pa.gov.br"
        password = "xpto1661WIN"
    return {"username": email, "password": password}

@pytest_asyncio.fixture(scope="function")
async def admin_token(async_client: AsyncClient, admin_credentials) -> str:
    """Token de autenticação do administrador"""
    response = await async_client.post("/auth/login", data=admin_credentials)
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        print(f"Credentials used: {admin_credentials}")
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]

@pytest_asyncio.fixture(scope="function")
async def admin_headers(admin_token: str):
    """Headers com token de administrador"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
async def outro_fiscal_user_id(get_db_connection):
    """Cria um segundo usuário fiscal para testes de transferência"""
    conn = await get_db_connection()

    # Busca o perfil Fiscal
    perfil_fiscal = await conn.fetchrow("SELECT id FROM perfil WHERE nome = 'Fiscal'")

    # Hash da senha
    from app.core.security import get_password_hash
    senha_hash = get_password_hash("senha123")

    # Cria o segundo fiscal
    fiscal_id = await conn.fetchval(
        """INSERT INTO usuario (nome, email, cpf, senha, perfil_id)
           VALUES ($1, $2, $3, $4, $5) RETURNING id""",
        "Carlos Fiscal Substituto", "carlos.fiscal@test.com", "98765432100",
        senha_hash, perfil_fiscal['id']
    )

    yield fiscal_id

    # Cleanup
    await conn.execute("UPDATE usuario SET ativo = FALSE WHERE id = $1", fiscal_id)