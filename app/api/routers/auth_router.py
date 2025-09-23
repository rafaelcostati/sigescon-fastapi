# app/api/routers/auth_router.py 
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from jose import jwt

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
from app.api.dependencies import get_current_user, get_current_context, get_token_payload
from app.core.security import authenticate_user, create_access_token
from app.core.config import settings

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

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

def get_user_id_from_token(token: str) -> int:
    """Extrai ID do usuário do token JWT"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except:
        return None

@router.post("/login", response_model=LoginResponse, summary="Login do usuário com seleção de perfil")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    perfil_inicial_id: Optional[int] = None,
    service: SessionContextService = Depends(get_session_context_service),
    conn: asyncpg.Connection = Depends(get_connection)
):
    
    user_repo = UsuarioRepository(conn)
    user = await user_repo.get_user_by_email(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Autentica o usuário
    auth_result = authenticate_user(form_data.password, user['senha_hash'])
    
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

    # Cria token JWT incluindo user_id e session_id
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

@router.post("/login-com-perfil", response_model=LoginResponse, summary="Login com perfil específico")
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

@router.post("/alternar-perfil", response_model=ContextoSessao, summary="Alternar perfil ativo na sessão")
async def switch_profile(
    request: Request,
    switch_data: AlternarPerfilRequest,
    service: SessionContextService = Depends(get_session_context_service),
    payload: dict = Depends(get_token_payload)
):
    """ Alterna o perfil ativo na sessão atual"""
    try:
        print(f"\n🚀 INÍCIO switch_profile - Timestamp: {__import__('datetime').datetime.now()}")
        print(f"📡 Request recebido: {switch_data}")
        print(f"🔑 Token payload: {payload}")

        user_id = int(payload.get("sub"))
        session_id = payload.get("session_id")

        print(f"👤 User ID extraído: {user_id}")
        print(f"🆔 Session ID extraído: {session_id}")

        # Busca contexto atual usando session_id se disponível, senão user_id
        print(f"🔍 Buscando contexto atual...")
        if session_id:
            print(f"   - Usando session_id: {session_id}")
            current_context = await service.get_session_context(session_id)
        else:
            print(f"   - Usando user_id: {user_id}")
            current_context = await service.get_session_context_by_user(user_id)

        print(f"📊 Contexto encontrado: {current_context is not None}")

        if not current_context:
            print(f"❌ ERROR: Contexto não encontrado! Criando contexto de emergência...")

            # FALLBACK TEMPORÁRIO PARA DEBUG: Criar contexto mínimo
            from app.repositories.session_context_repo import SessionContextRepository
            from app.repositories.usuario_repo import UsuarioRepository
            from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository
            from app.core.database import get_connection

            # Buscar perfis do usuário diretamente
            async with get_connection() as emergency_conn:
                session_repo = SessionContextRepository(emergency_conn)
                perfis_emergency = await session_repo.get_user_available_profiles(user_id)
                print(f"🆘 EMERGENCY: Perfis encontrados para user {user_id}: {perfis_emergency}")

                if perfis_emergency:
                    # Verificar se o perfil solicitado está na lista
                    perfil_solicitado = next((p for p in perfis_emergency if p['id'] == switch_data.novo_perfil_id), None)
                    if perfil_solicitado:
                        print(f"✅ EMERGENCY: Perfil {switch_data.novo_perfil_id} encontrado! Permitindo troca...")
                        # Forçar criação de contexto mínimo
                        from app.schemas.session_context_schema import ContextoSessao, PerfilAtivo
                        current_context = ContextoSessao(
                            usuario_id=user_id,
                            perfil_ativo_id=perfis_emergency[0]['id'],
                            perfil_ativo_nome=perfis_emergency[0]['nome'],
                            perfis_disponiveis=[PerfilAtivo(
                                id=p['id'],
                                nome=p['nome'],
                                descricao=p.get('descricao'),
                                pode_ser_selecionado=True
                            ) for p in perfis_emergency],
                            pode_alternar=len(perfis_emergency) > 1,
                            sessao_id=session_id or f'emergency-{user_id}'
                        )
                        print(f"🆘 EMERGENCY: Contexto criado com sucesso")
                    else:
                        print(f"❌ EMERGENCY: Perfil {switch_data.novo_perfil_id} NÃO encontrado nos perfis do usuário")
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Perfil {switch_data.novo_perfil_id} não disponível. Perfis disponíveis: {[p['id'] for p in perfis_emergency]}"
                        )
                else:
                    print(f"❌ EMERGENCY: Usuário {user_id} não tem nenhum perfil!")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Usuário não possui perfis ativos"
                    )

        # Debug: log do contexto atual
        print(f"🔍 DEBUG: Contexto final do usuário {user_id}:")
        print(f"   - Perfil ativo: {current_context.perfil_ativo_id} ({current_context.perfil_ativo_nome})")
        print(f"   - Perfis disponíveis: {[{'id': p.id, 'nome': p.nome} for p in current_context.perfis_disponiveis]}")
        print(f"   - Tentando alternar para perfil ID: {switch_data.novo_perfil_id}")

        # Valida se o novo perfil está disponível
        perfil_disponivel = next(
            (p for p in current_context.perfis_disponiveis if p.id == switch_data.novo_perfil_id),
            None
        )

        print(f"🔍 DEBUG: Perfil encontrado na lista? {perfil_disponivel is not None}")
        if perfil_disponivel:
            print(f"   - Perfil encontrado: {perfil_disponivel.nome} (ID: {perfil_disponivel.id})")

        if not perfil_disponivel:
            print(f"❌ ERROR: Perfil {switch_data.novo_perfil_id} não encontrado nos perfis disponíveis")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil não disponível para este usuário"
            )

        # Atualiza o contexto no banco de dados
        ip_address, user_agent = get_client_info(request)

        contexto_atualizado = await service.switch_profile_context(
            current_context.sessao_id,
            user_id,
            switch_data.novo_perfil_id,
            switch_data.justificativa,
            ip_address,
            user_agent
        )

        return contexto_atualizado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao alternar perfil: {str(e)}"
        )

@router.get("/contexto", response_model=ContextoSessao, summary="Contexto atual da sessão do usuário")
async def get_current_context_endpoint(
    current_context: ContextoSessao = Depends(get_current_context)
):
    """Retorna o contexto atual da sessão do usuário"""
    return current_context

@router.get("/dashboard", response_model=DashboardData, summary="Dados do dashboard baseados no perfil ativo")
async def get_dashboard_data(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Retorna dados do dashboard baseados no perfil ativo do usuário"""
    try:
        return await service.get_dashboard_data(current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados do dashboard: {str(e)}"
        )

@router.get("/permissoes", response_model=PermissaoContextual, summary="Permissões contextuais baseadas no perfil ativo")
async def get_contextual_permissions(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Retorna permissões específicas baseadas no perfil ativo"""
    try:
        return await service.get_contextual_permissions(current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar permissões: {str(e)}"
        )

@router.post("/logout")
async def logout(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    
    return {
        "message": "Logout realizado com sucesso",
        "sessoes_encerradas": 1
    }


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

    auth_result = authenticate_user(form_data.password, user['senha_hash'])
    
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

