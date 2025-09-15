# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha fornecida corresponde ao hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        try:
            from werkzeug.security import check_password_hash
            return check_password_hash(hashed_password, plain_password)
        except ImportError:
            return False

def get_password_hash(password: str) -> str:
    """Gera o hash de uma senha."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um novo token de acesso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Função auxiliar para migrar senhas antigas do Flask para o novo formato
def migrate_password_if_needed(plain_password: str, stored_hash: str) -> tuple[bool, Optional[str]]:
    """
    Verifica a senha e retorna se é válida e um novo hash se necessário.
    Retorna: (is_valid, new_hash_or_none)
    """
    try:
        # Primeiro tenta verificar com o contexto atual (bcrypt)
        if pwd_context.verify(plain_password, stored_hash):
            # Verifica se precisa de rehash (atualização)
            if pwd_context.needs_update(stored_hash):
                return True, get_password_hash(plain_password)
            return True, None
    except Exception:
        # Se der erro, a senha pode ser do formato Werkzeug
        pass
    
    # Tenta verificar com werkzeug (senhas antigas do Flask)
    try:
        from werkzeug.security import check_password_hash
        if check_password_hash(stored_hash, plain_password):
            # Senha válida, mas no formato antigo - cria novo hash
            return True, get_password_hash(plain_password)
    except (ImportError, Exception):
        pass
    
    return False, None

def authenticate_user(password: str, stored_hash: str) -> dict:
    """
    Autentica o usuário e retorna informações sobre a necessidade de migração.
    Retorna: {
        'is_valid': bool,
        'needs_migration': bool,
        'new_hash': str or None
    }
    """
    try:
        # Tenta primeiro com bcrypt (senhas novas)
        if pwd_context.verify(password, stored_hash):
            needs_update = pwd_context.needs_update(stored_hash)
            return {
                'is_valid': True,
                'needs_migration': needs_update,
                'new_hash': get_password_hash(password) if needs_update else None
            }
    except Exception:
        # Hash não reconhecido pelo passlib, deve ser do Werkzeug
        pass
    
    # Tenta com Werkzeug (senhas antigas do Flask)
    try:
        from werkzeug.security import check_password_hash
        if check_password_hash(stored_hash, password):
            return {
                'is_valid': True,
                'needs_migration': True,
                'new_hash': get_password_hash(password)
            }
    except Exception:
        pass
    
    return {
        'is_valid': False,
        'needs_migration': False,
        'new_hash': None
    }