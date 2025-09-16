# app/api/exception_handlers.py
import logging
from typing import Any, Dict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
import asyncpg

from app.core.exceptions import (
    SigesconException, 
    EXCEPTION_STATUS_MAPPING,
    DatabaseException
)

logger = logging.getLogger(__name__)

async def sigescon_exception_handler(request: Request, exc: SigesconException) -> JSONResponse:
    """Handler para exceções customizadas do SIGESCON"""
    
    status_code = EXCEPTION_STATUS_MAPPING.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log do erro
    logger.error(
        f"SigesconException: {exc.__class__.__name__} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "error_type": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "timestamp": str(request.state.timestamp if hasattr(request.state, 'timestamp') else '')
        }
    )

async def database_exception_handler(request: Request, exc: asyncpg.PostgresError) -> JSONResponse:
    """Handler específico para erros de banco PostgreSQL"""
    
    logger.error(
        f"Database error: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "sqlstate": getattr(exc, 'sqlstate', None)
        }
    )
    
    # Mapeia códigos de erro específicos do PostgreSQL
    error_mappings = {
        "23505": "Violação de restrição única - dados duplicados",
        "23503": "Violação de chave estrangeira - registro relacionado não encontrado", 
        "23502": "Campo obrigatório não pode ser nulo",
        "42703": "Coluna não encontrada",
        "42P01": "Tabela não encontrada",
    }
    
    sqlstate = getattr(exc, 'sqlstate', None)
    user_message = error_mappings.get(sqlstate, "Erro interno do banco de dados")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_type": "DatabaseError",
            "message": user_message,
            "details": {
                "sqlstate": sqlstate,
                "original_error": str(exc) if logger.level <= logging.DEBUG else None
            },
            "path": request.url.path
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler para erros de validação do Pydantic"""
    
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "body": exc.body
        }
    )
    
    # Reformata os erros para ficar mais user-friendly
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "error_type": "ValidationError",
            "message": "Dados inválidos fornecidos",
            "details": {
                "validation_errors": formatted_errors,
                "total_errors": len(formatted_errors)
            },
            "path": request.url.path
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler para HTTPExceptions padrão do FastAPI"""
    
    logger.info(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_type": "HTTPError",
            "message": exc.detail,
            "details": {},
            "path": request.url.path
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para exceções não mapeadas"""
    
    logger.exception(
        f"Unhandled exception: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )
    
    # Em produção, não expor detalhes internos
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_type": "InternalServerError",
            "message": "Erro interno do servidor. Por favor, tente novamente mais tarde.",
            "details": {
                "exception_type": type(exc).__name__,
                "traceback": str(exc) if logger.level <= logging.DEBUG else None
            },
            "path": request.url.path,
            "support_contact": "COLOCAR UM EMAIL"
        }
    )

# app/core/validators.py
import re
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from app.core.exceptions import ValidationException

class SigesconValidators:
    """Validadores customizados para o sistema SIGESCON"""
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """Valida CPF brasileiro"""
        cpf = re.sub(r'\D', '', cpf)  # Remove caracteres não numéricos
        
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais (exceto 00000000000 que usamos para o admin)
        if cpf == '00000000000' or len(set(cpf)) == 1:
            return cpf == '00000000000'  # Permite apenas o CPF do admin
        
        # Validação dos dígitos verificadores
        for i in range(9, 11):
            soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
            digito = (soma * 10) % 11
            if digito == 10:
                digito = 0
            if int(cpf[i]) != digito:
                return False
        
        return True
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """Valida CNPJ brasileiro"""
        cnpj = re.sub(r'\D', '', cnpj)
        
        if len(cnpj) != 14:
            return False
        
        # Verifica se todos os dígitos são iguais
        if len(set(cnpj)) == 1:
            return False
        
        # Cálculo do primeiro dígito verificador
        soma = sum(int(cnpj[i]) * (5 - i if i < 4 else 13 - i) for i in range(12))
        digito1 = 11 - (soma % 11)
        if digito1 >= 10:
            digito1 = 0
        
        # Cálculo do segundo dígito verificador
        soma = sum(int(cnpj[i]) * (6 - i if i < 5 else 14 - i) for i in range(13))
        digito2 = 11 - (soma % 11)
        if digito2 >= 10:
            digito2 = 0
        
        return int(cnpj[12]) == digito1 and int(cnpj[13]) == digito2
    
    @staticmethod
    def validate_contract_dates(data_inicio: date, data_fim: date) -> None:
        """Valida datas de contrato"""
        hoje = date.today()
        
        if data_inicio >= data_fim:
            raise ValidationException(
                "Data de início deve ser anterior à data de fim",
                {"data_inicio": data_inicio, "data_fim": data_fim}
            )
        
        # Permite contratos retroativos, mas alerta para contratos muito antigos
        if (hoje - data_inicio).days > 365 * 5:  # 5 anos
            raise ValidationException(
                "Data de início não pode ser superior a 5 anos no passado",
                {"data_inicio": data_inicio, "limite": hoje - timedelta(days=365*5)}
            )
        
        # Permite contratos com prazo muito longo, mas alerta
        if (data_fim - data_inicio).days > 365 * 10:  # 10 anos
            raise ValidationException(
                "Contrato não pode ter prazo superior a 10 anos",
                {"duracao_anos": (data_fim - data_inicio).days / 365}
            )
    
    @staticmethod
    def validate_file_upload(filename: str, content_type: str, size_bytes: int) -> None:
        """Valida arquivo de upload"""
        # Extensões permitidas
        allowed_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.odt', '.ods'}
        
        file_ext = '.' + filename.split('.')[-1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationException(
                f"Tipo de arquivo não permitido: {file_ext}",
                {
                    "filename": filename,
                    "allowed_extensions": list(allowed_extensions)
                }
            )
        
        # Tamanho máximo: 50MB
        max_size = 50 * 1024 * 1024  # 50MB em bytes
        if size_bytes > max_size:
            raise ValidationException(
                f"Arquivo muito grande: {size_bytes / (1024*1024):.1f}MB",
                {
                    "size_mb": size_bytes / (1024*1024),
                    "max_size_mb": max_size / (1024*1024)
                }
            )
        
        # Verifica nome do arquivo
        if len(filename) > 255:
            raise ValidationException(
                "Nome do arquivo muito longo (máximo 255 caracteres)",
                {"filename_length": len(filename)}
            )
        
        # Caracteres perigosos no nome do arquivo
        dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        if any(char in filename for char in dangerous_chars):
            raise ValidationException(
                "Nome do arquivo contém caracteres não permitidos",
                {
                    "filename": filename,
                    "forbidden_chars": dangerous_chars
                }
            )