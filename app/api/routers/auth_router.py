# app/api/routers/auth_router.py - ATUALIZADO COM CONTEXTO DE SESSÃO
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

from app.core.database import get_connection
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository
from app.repositories.session_context_repo import SessionContextRepository
from app.repositories.contrato_repo import ContratoRepository
from app.services.session_context_service import SessionContextService
from app.schemas.token_schema import Token
from app.schemas.session_context_schema import (
    LoginResponse, LoginComPerfilRequest, AlternarPerfilRequest,
    ContextoSessao, DashboardData, PermissaoContextual
)
from app.schemas.usuario_schema import Usuario
from app.api.dependencies import get_current_user
from app.core.security import authenticate_user, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

# Dependência para o serviço de contexto
def get_session_context_service(conn: asyncpg.Connection = Depends(get_connection)) -> SessionContextService:
    return SessionContextService(
        session_repo=SessionContextRepository(conn),
        usuario_repo=UsuarioRepository(conn),
        usuario_perfil_repo=UsuarioPerfilRepository(conn),
        contrato_repo=ContratoRepository(conn)
    )

def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extrai informações do cliente (IP e User-Agent)"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent

@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    perfil_inicial_id: Optional[int] = None,
    service: SessionContextService = Depends(get_session_context_service),
    conn: asyncpg.Connection = Depends(get_connection)
):
    """
    Login com seleção automática ou manual de perfil inicial.
    
    Se o usuário tem múltiplos perfis:
    - Com perfil_inicial_id: Usa o perfil especificado
    - Sem perfil_inicial_id: Usa o perfil de maior prioridade
    """
    user_repo = UsuarioRepository(conn)
    user = await user_repo.get_user_by_email(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Autentica o usuário
    auth_result = authenticate_user(form_data.password, user['senha'])
    
    if not auth_result['is_valid']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Se a senha precisa ser migrada, atualiza no banco
    if auth_result['needs_migration'] and auth_result['new_hash']:
        await user_repo.update_user_password_hash(user['id'], auth_result['new_hash'])

    # Obter informações do cliente
    ip_address, user_agent = get_client_info(request)

    # Cria contexto de sessão
    try:
        contexto = await service.create_session_context(
            usuario_id=user['id'],
            perfil_inicial_id=perfil_inicial_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar contexto de sessão: {str(e)}"
        )

    # Cria token JWT incluindo sessao_id
    access_token = create_access_token(data={
        "sub": str(user['id']),
        "session_id": contexto.sessao_id
    })

    # Verifica se precisa de seleção manual de perfil
    requer_selecao = len(contexto.perfis_disponiveis) > 1 and perfil_inicial_id is None
    
    mensagem = None
    if requer_selecao:
        mensagem = "Usuário possui múltiplos perfis. Perfil padrão selecionado automaticamente."
    elif len(contexto.perfis_disponiveis) > 1:
        mensagem = f"Login realizado como {contexto.perfil_ativo_nome}. Você pode alternar perfis a qualquer momento."

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        contexto_sessao=contexto,
        requer_selecao_perfil=requer_selecao,
        mensagem=mensagem
    )

@router.post("/login-com-perfil", response_model=LoginResponse)
async def login_with_specific_profile(
    request: Request,
    login_data: LoginComPerfilRequest,
    service: SessionContextService = Depends(get_session_context_service),
    conn: asyncpg.Connection = Depends(get_connection)
):
    """Login especificando um perfil específico no corpo da requisição"""
    
    # Simula OAuth2PasswordRequestForm para reutilizar lógica
    from fastapi.security import OAuth2PasswordRequestForm
    
    # Cria form_data simulado
    class FakeFormData:
        def __init__(self, username: str, password: str):
            self.username = username
            self.password = password
    
    fake_form = FakeFormData(login_data.email, login_data.senha)
    
    # Reutiliza a lógica do login normal
    return await login_for_access_token(
        request=request,
        form_data=fake_form,
        perfil_inicial_id=login_data.perfil_inicial_id,
        service=service,
        conn=conn
    )

@router.post("/alternar-perfil", response_model=ContextoSessao)
async def switch_profile(
    request: Request,
    switch_data: AlternarPerfilRequest,
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Alterna o perfil ativo na sessão atual.
    
    Permite que usuários com múltiplos perfis alternem entre eles
    sem precisar fazer logout/login.
    """
    # Extrai session_id do token (implementar na dependência get_current_user)
    # Por enquanto, vamos buscar pela sessão ativa do usuário
    
    # Busca sessões ativas do usuário
    session_repo = SessionContextRepository(await get_connection().__anext__())
    active_sessions = await session_repo.get_user_active_sessions(current_user.id)
    
    if not active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma sessão ativa encontrada"
        )
    
    # Usa a sessão mais recente
    sessao_id = active_sessions[0]['sessao_id']
    
    ip_address, user_agent = get_client_info(request)
    
    return await service.switch_profile(
        sessao_id=sessao_id,
        request=switch_data,
        ip_address=ip_address,
        user_agent=user_agent
    )

@router.get("/contexto", response_model=ContextoSessao)
async def get_current_context(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna o contexto atual da sessão do usuário.
    
    Inclui perfil ativo, perfis disponíveis e informações da sessão.
    """
    # Busca sessão ativa (mesmo processo do endpoint anterior)
    session_repo = SessionContextRepository(await get_connection().__anext__())
    active_sessions = await session_repo.get_user_active_sessions(current_user.id)
    
    if not active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contexto de sessão não encontrado"
        )
    
    sessao_id = active_sessions[0]['sessao_id']
    context = await service.get_session_context(sessao_id)
    
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contexto de sessão expirado"
        )
    
    return context

@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna dados do dashboard baseados no perfil ativo do usuário.
    
    Os widgets, menus e estatísticas variam conforme o perfil.
    """
    # Busca sessão ativa
    session_repo = SessionContextRepository(await get_connection().__anext__())
    active_sessions = await session_repo.get_user_active_sessions(current_user.id)
    
    if not active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    sessao_id = active_sessions[0]['sessao_id']
    return await service.get_dashboard_data(sessao_id)

@router.get("/permissoes", response_model=PermissaoContextual)
async def get_contextual_permissions(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna permissões específicas baseadas no perfil ativo.
    
    O frontend pode usar essas informações para mostrar/ocultar funcionalidades.
    """
    # Busca sessão ativa
    session_repo = SessionContextRepository(await get_connection().__anext__())
    active_sessions = await session_repo.get_user_active_sessions(current_user.id)
    
    if not active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    sessao_id = active_sessions[0]['sessao_id']
    return await service.get_contextual_permissions(sessao_id)

@router.post("/logout")
async def logout(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Realiza logout encerrando a sessão ativa.
    """
    # Busca e encerra todas as sessões ativas do usuário
    session_repo = SessionContextRepository(await get_connection().__anext__())
    active_sessions = await session_repo.get_user_active_sessions(current_user.id)
    
    logout_count = 0
    for session in active_sessions:
        if await service.logout_session(session['sessao_id']):
            logout_count += 1
    
    return {
        "message": "Logout realizado com sucesso",
        "sessoes_encerradas": logout_count
    }

# Mantém endpoint original para compatibilidade
@router.post("/login-legacy", response_model=Token)
async def login_legacy(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: asyncpg.Connection = Depends(get_connection)
):
    """Endpoint de login original (mantido para compatibilidade)"""
    user_repo = UsuarioRepository(conn)
    user = await user_repo.get_user_by_email(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_result = authenticate_user(form_data.password, user['senha'])
    
    if not auth_result['is_valid']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if auth_result['needs_migration'] and auth_result['new_hash']:
        await user_repo.update_user_password_hash(user['id'], auth_result['new_hash'])

    access_token = create_access_token(data={"sub": str(user['id'])})

    return {"access_token": access_token, "token_type": "bearer"}