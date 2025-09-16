# app/core/exceptions.py
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class SigesconException(Exception):
    """Exceção base para o sistema SIGESCON"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class BusinessRuleException(SigesconException):
    """Exceção para violações de regras de negócio"""
    pass

class ValidationException(SigesconException):
    """Exceção para erros de validação"""
    pass

class ResourceNotFoundException(SigesconException):
    """Exceção para recursos não encontrados"""
    pass

class PermissionDeniedException(SigesconException):
    """Exceção para acesso negado"""
    pass

class DatabaseException(SigesconException):
    """Exceção para erros de banco de dados"""
    pass

class FileUploadException(SigesconException):
    """Exceção para erros de upload de arquivo"""
    pass

class EmailException(SigesconException):
    """Exceção para erros de envio de email"""
    pass

# Mapeamento de exceções para códigos HTTP
EXCEPTION_STATUS_MAPPING = {
    BusinessRuleException: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ValidationException: status.HTTP_400_BAD_REQUEST,
    ResourceNotFoundException: status.HTTP_404_NOT_FOUND,
    PermissionDeniedException: status.HTTP_403_FORBIDDEN,
    DatabaseException: status.HTTP_500_INTERNAL_SERVER_ERROR,
    FileUploadException: status.HTTP_400_BAD_REQUEST,
    EmailException: status.HTTP_500_INTERNAL_SERVER_ERROR,
}

