# app/core/database.py
import asyncpg
from .config import settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Usaremos um pool de conexões para eficiência
pool = None

async def get_db_pool():
    """
    Retorna o pool de conexões, criando-o se não existir.
    """
    global pool
    if pool is None:
        try:
            pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=1,
                max_size=10,  # Reduzido para testes
                command_timeout=60
            )
            logger.info("Pool de conexões do banco criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar pool de conexões: {e}")
            raise
    return pool

async def get_connection():
    """
    Obtém uma conexão do pool.
    """
    db_pool = await get_db_pool()
    connection = None
    try:
        async with db_pool.acquire() as connection:
            yield connection
    except Exception as e:
        logger.error(f"Erro ao obter conexão do pool: {e}")
        if connection:
            # Força o fechamento da conexão problemática
            try:
                await connection.close()
            except:
                pass
        raise
    finally:
        # Garante que a conexão seja devolvida ao pool
        if connection and not connection.is_closed():
            try:
                await db_pool.release(connection)
            except:
                pass

async def close_db_pool():
    """
    Fecha o pool de conexões.
    """
    global pool
    if pool:
        try:
            await pool.close()
            logger.info("Pool de conexões fechado")
        except Exception as e:
            logger.error(f"Erro ao fechar pool: {e}")
        finally:
            pool = None