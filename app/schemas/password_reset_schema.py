# app/schemas/password_reset_schema.py

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class ForgotPasswordRequest(BaseModel):
    """Schema para solicitação de reset de senha"""
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@exemplo.com"
            }
        }

class ForgotPasswordResponse(BaseModel):
    """Schema para resposta de solicitação de reset"""
    success: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Solicitação enviada! Instruções para recuperar sua senha foram registradas."
            }
        }

class ResetPasswordRequest(BaseModel):
    """Schema para reset de senha com token"""
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('A senha deve ter pelo menos 6 caracteres')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_example_123456789",
                "new_password": "nova_senha_123"
            }
        }

class ResetPasswordResponse(BaseModel):
    """Schema para resposta de reset de senha"""
    success: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Senha alterada com sucesso!"
            }
        }

class ValidateTokenRequest(BaseModel):
    """Schema para validação de token"""
    token: str

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_example_123456789"
            }
        }

class ValidateTokenResponse(BaseModel):
    """Schema para resposta de validação de token"""
    valid: bool
    message: str
    user_email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "message": "Token válido",
                "user_email": "usuario@exemplo.com"
            }
        }

class PasswordResetToken(BaseModel):
    """Schema para representar um token de reset de senha"""
    id: int
    token: str
    usuario_id: int
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True