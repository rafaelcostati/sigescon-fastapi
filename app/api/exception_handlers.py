# app/api/exception_handlers.py
import logging
import base64
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

def safe_serialize_request_body(body: Any) -> Any:
    """
    Serializa o corpo da requisição de forma segura para JSON.
    Converte bytes para uma representação segura.
    """
    if body is None:
        return None
    
    if isinstance(body, bytes):
        # Para arquivos de upload, não incluir o conteúdo completo do arquivo
        # Apenas informações básicas sobre o tamanho
        return {
            "type": "binary_data",
            "size_bytes": len(body),
            "preview": f"Binary data ({len(body)} bytes)"
        }
    
    if isinstance(body, (str, int, float, bool, list, dict)):
        return body
    
    # Para outros tipos, converter para string
    return str(body)

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
    
    # Mensagem específica para número de contrato duplicado
    if sqlstate == "23505" and "idx_unique_contrato_nr_contrato_ativo" in str(exc):
        user_message = "Este número de contrato já está em uso. Por favor, escolha um número diferente."
    
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
    
    # Serializa o corpo da requisição de forma segura
    safe_body = safe_serialize_request_body(exc.body)
    
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "body_info": safe_body
        }
    )
    
    # Reformata os erros para ficar mais user-friendly
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        
        # Sanitiza o input para evitar problemas de serialização
        error_input = error.get("input")
        if isinstance(error_input, bytes):
            error_input = f"<binary data: {len(error_input)} bytes>"
        elif error_input is not None and not isinstance(error_input, (str, int, float, bool, list, dict)):
            error_input = str(error_input)
        
        formatted_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error_input
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "error_type": "ValidationError",
            "message": "Dados inválidos fornecidos",
            "details": {
                "validation_errors": formatted_errors,
                "total_errors": len(formatted_errors),
                "body_info": safe_body
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
        },
        headers=exc.headers
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
            "support_contact": "sememailnomomento@email.com"
        }
    )