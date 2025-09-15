# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict # <-- IMPORTAR SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Dicionário de configuração do Pydantic v2
    model_config = SettingsConfigDict(env_file=".env", extra='ignore') # <-- ADICIONAR ESTA LINHA

    # Configuração do Banco de Dados
    DATABASE_URL: str

    # Configuração de Autenticação JWT
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Credenciais do Admin (para seeder ou lógicas futuras)
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None

    # Configuração do Servidor de Email (SMTP)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SENDER_EMAIL: Optional[str] = None
    SENDER_PASSWORD: Optional[str] = None

 

settings = Settings()