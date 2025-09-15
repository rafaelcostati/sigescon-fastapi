# app/core/database.py
import asyncpg
from .config import settings

# Usaremos um pool de conexões para eficiência
pool = None

async def get_db_pool():
    """
    Retorna o pool de conexões, criando-o se não existir.
    """
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=20
        )
    return pool

async def get_connection():
    """
    Obtém uma conexão do pool.
    """
    db_pool = await get_db_pool()
    async with db_pool.acquire() as connection:
        yield connection

async def close_db_pool():
    """
    Fecha o pool de conexões.
    """
    global pool
    if pool:
        await pool.close()
        pool = None