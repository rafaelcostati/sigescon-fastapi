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