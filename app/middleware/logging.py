# app/middleware/logging.py
import logging
import sys
from pathlib import Path

def setup_logging():
    """Configura sistema de logging da aplicação"""
    
    # Cria diretório de logs se não existir
    Path("logs").mkdir(exist_ok=True)
    
    # Configuração para logs gerais
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Logger específico para erros de banco
    db_logger = logging.getLogger("database")
    db_handler = logging.FileHandler("logs/database.log")
    db_formatter = logging.Formatter(
        '%(asctime)s - DATABASE - %(levelname)s - %(message)s'
    )
    db_handler.setFormatter(db_formatter)
    db_logger.addHandler(db_handler)
    
    # Logger específico para autenticação
    auth_logger = logging.getLogger("auth")
    auth_handler = logging.FileHandler("logs/auth.log")
    auth_formatter = logging.Formatter(
        '%(asctime)s - AUTH - %(levelname)s - %(message)s'
    )
    auth_handler.setFormatter(auth_formatter)
    auth_logger.addHandler(auth_handler)

