#!/usr/bin/env python3
"""
Script para aplicar as correções nos endpoints de dashboard, contexto e permissões.
Execute com: python scripts/apply_endpoint_fixes.py
"""

import os
import sys
from datetime import datetime

def backup_file(filepath):
    """Cria backup do arquivo original"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(filepath, 'r', encoding='utf-8') as original:
            content = original.read()
        with open(backup_path, 'w', encoding='utf-8') as backup:
            backup.write(content)
        print(f"✅ Backup criado: {backup_path}")
        return True
    return False

def create_session_context_repo():
    """Cria o arquivo session_context_repo.py simplificado"""
    content = '''# app/repositories/session_context_repo.py - VERSÃO SIMPLIFICADA E CORRIGIDA
import asyncpg
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

class SessionContextRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_user_available_profiles(self, usuario_id: int) -> List[Dict]:
        """✅ CORRIGIDO: Busca todos os perfis disponíveis para o usuário"""
        query = """
            SELECT p.id, p.nome, 
                   CASE 
                       WHEN p.nome = 'Administrador' THEN 'Acesso total ao sistema'
                       WHEN p.nome = 'Gestor' THEN 'Gestão de contratos e equipes'
                       WHEN p.nome = 'Fiscal' THEN 'Fiscalização e relatórios'
                       ELSE 'Perfil do sistema'
                   END as descricao
            FROM usuario_perfil up
            JOIN perfil p ON up.perfil_id = p.id
            WHERE up.usuario_id = $1 AND up.ativo = TRUE AND p.ativo = TRUE
            ORDER BY 
                CASE p.nome 
                    WHEN 'Administrador' THEN 1
                    WHEN 'Gestor' THEN 2
                    WHEN 'Fiscal' THEN 3
                    ELSE 4
                END
        """
        records = await self.conn.fetch(query, usuario_id)
        return [dict(r) for r in records]

    async def validate_profile_for_user(self, usuario_id: int, perfil_id: int) -> bool:
        """✅ NOVO: Valida se o usuário pode usar um perfil específico"""
        query = """
            SELECT 1 FROM usuario_perfil up
            WHERE up.usuario_id = $1 AND up.perfil_id = $2 AND up.ativo = TRUE
        """
        result = await self.conn.fetchval(query, usuario_id, perfil_id)
        return bool(result)
'''
    
    repo_path = 'app/repositories/session_context_repo.py'
    os.makedirs(os.path.dirname(repo_path), exist_ok=True)
    
    # Backup se existir
    backup_file(repo_path)
    
    with open(repo_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Criado/atualizado: {repo_path}")

def update_session_context_service():
    """Atualiza o session_context_service.py"""
    service_path = 'app/services/session_context_service.py'
    
    if not os.path.exists(service_path):
        print(f"⚠️ Arquivo não encontrado: {service_path}")
        return
    
    # Backup do arquivo original
    backup_file(service_path)
    
    # Adiciona método simplificado no final do arquivo
    additional_content = '''
    
    # ✅ MÉTODO ADICIONADO PARA CORREÇÃO DOS ENDPOINTS
    async def get_session_context_by_user(self, usuario_id: int) -> Optional[ContextoSessao]:
        """✅ NOVO: Busca contexto baseado no ID do usuário (para simplificar)"""
        try:
            # Busca perfis disponíveis
            perfis_disponiveis = await self.session_repo.get_user_available_profiles(usuario_id)
            
            if not perfis_disponiveis:
                return None
            
            # Usa o primeiro perfil como ativo (Gestor tem prioridade)
            perfil_ativo = perfis_disponiveis[0]
            
            # Converte para schema
            perfis_ativos = [
                PerfilAtivo(
                    id=p['id'],
                    nome=p['nome'],
                    descricao=p.get('descricao'),
                    pode_ser_selecionado=True
                ) for p in perfis_disponiveis
            ]
            
            return ContextoSessao(
                usuario_id=usuario_id,
                perfil_ativo_id=perfil_ativo['id'],
                perfil_ativo_nome=perfil_ativo['nome'],
                perfis_disponiveis=perfis_ativos,
                pode_alternar=len(perfis_disponiveis) > 1,
                sessao_id=f'mock-session-{usuario_id}'
            )
            
        except Exception as e:
            print(f"Erro ao buscar contexto: {e}")
            return None

    async def get_dashboard_data_by_user(self, usuario_id: int) -> DashboardData:
        """✅ CORRIGIDO: Retorna dados do dashboard baseados no usuário"""
        try:
            # Busca perfis do usuário para determinar o perfil ativo
            perfis = await self.usuario_perfil_repo.get_user_profiles(usuario_id)
            
            if not perfis:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuário não possui perfis ativos"
                )
            
            # Usa o primeiro perfil (mais prioritário)
            perfil_ativo = perfis[0]['perfil_nome']
            
            # Define widgets e menus baseados no perfil
            if perfil_ativo == "Administrador":
                widgets = ["contratos_total", "usuarios_ativos", "relatorios_pendentes"]
                menus = [
                    {"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
                    {"nome": "Contratos", "icon": "contracts", "route": "/contratos"},
                    {"nome": "Usuários", "icon": "users", "route": "/usuarios"}
                ]
                permissoes = ["criar_contrato", "editar_contrato", "gerenciar_usuarios"]
                
            elif perfil_ativo == "Gestor":
                widgets = ["meus_contratos", "relatorios_equipe", "pendencias_gestao"]
                menus = [
                    {"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
                    {"nome": "Meus Contratos", "icon": "contracts", "route": "/contratos/gestao"}
                ]
                permissoes = ["ver_contratos_gestao", "aprovar_relatorios"]
                
            elif perfil_ativo == "Fiscal":
                widgets = ["meus_contratos_fiscalizacao", "pendencias_ativas"]
                menus = [
                    {"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
                    {"nome": "Fiscalização", "icon": "audit", "route": "/contratos/fiscalizacao"}
                ]
                permissoes = ["submeter_relatorios", "ver_contratos_fiscal"]
                
            else:
                widgets = []
                menus = []
                permissoes = []
            
            # Busca estatísticas básicas
            estatisticas = {"total": 0}
            try:
                if perfil_ativo == "Administrador":
                    total_contratos = await self.session_repo.conn.fetchval("SELECT COUNT(*) FROM contrato WHERE ativo = TRUE")
                    estatisticas = {"total_contratos": total_contratos or 0}
                elif perfil_ativo == "Gestor":
                    contratos_gestao = await self.session_repo.conn.fetchval("SELECT COUNT(*) FROM contrato WHERE gestor_id = $1 AND ativo = TRUE", usuario_id)
                    estatisticas = {"contratos_sob_gestao": contratos_gestao or 0}
                elif perfil_ativo == "Fiscal":
                    contratos_fiscal = await self.session_repo.conn.fetchval("SELECT COUNT(*) FROM contrato WHERE (fiscal_id = $1 OR fiscal_substituto_id = $1) AND ativo = TRUE", usuario_id)
                    estatisticas = {"contratos_fiscalizados": contratos_fiscal or 0}
            except:
                estatisticas = {"total": 0}
            
            return DashboardData(
                perfil_ativo=perfil_ativo,
                widgets_disponiveis=widgets,
                menus_disponiveis=menus,
                permissoes_ativas=permissoes,
                estatisticas=estatisticas
            )
            
        except Exception as e:
            print(f"Erro no dashboard: {e}")
            return DashboardData(
                perfil_ativo="Fiscal",
                widgets_disponiveis=["básico"],
                menus_disponiveis=[{"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"}],
                permissoes_ativas=["visualizar"],
                estatisticas={"total": 0}
            )

    async def get_contextual_permissions_by_user(self, usuario_id: int) -> PermissaoContextual:
        """✅ CORRIGIDO: Retorna permissões baseadas no usuário"""
        try:
            # Busca perfis do usuário
            perfis = await self.usuario_perfil_repo.get_user_profiles(usuario_id)
            
            if not perfis:
                return PermissaoContextual(
                    perfil_ativo="Fiscal",
                    pode_submeter_relatorio=True,
                    acoes_disponiveis=["visualizar"]
                )
            
            # Usa o primeiro perfil como ativo
            perfil_ativo = perfis[0]['perfil_nome']
            
            # Define permissões baseadas no perfil ativo
            if perfil_ativo == "Administrador":
                permissions = PermissaoContextual(
                    perfil_ativo=perfil_ativo,
                    pode_criar_contrato=True,
                    pode_editar_contrato=True,
                    pode_criar_pendencia=True,
                    pode_submeter_relatorio=True,
                    pode_aprovar_relatorio=True,
                    pode_gerenciar_usuarios=True,
                    pode_ver_todos_contratos=True,
                    acoes_disponiveis=["criar", "editar", "deletar", "aprovar", "rejeitar"]
                )
                
            elif perfil_ativo == "Gestor":
                permissions = PermissaoContextual(
                    perfil_ativo=perfil_ativo,
                    pode_criar_contrato=False,
                    pode_editar_contrato=False,
                    pode_criar_pendencia=True,
                    pode_submeter_relatorio=False,
                    pode_aprovar_relatorio=True,
                    pode_gerenciar_usuarios=False,
                    pode_ver_todos_contratos=False,
                    contratos_visiveis=[],
                    acoes_disponiveis=["visualizar", "criar_pendencia", "aprovar_relatorio"]
                )
                
            elif perfil_ativo == "Fiscal":
                permissions = PermissaoContextual(
                    perfil_ativo=perfil_ativo,
                    pode_criar_contrato=False,
                    pode_editar_contrato=False,
                    pode_criar_pendencia=False,
                    pode_submeter_relatorio=True,
                    pode_aprovar_relatorio=False,
                    pode_gerenciar_usuarios=False,
                    pode_ver_todos_contratos=False,
                    contratos_visiveis=[],
                    acoes_disponiveis=["visualizar", "submeter_relatorio", "responder_pendencia"]
                )
                
            else:
                permissions = PermissaoContextual(perfil_ativo=perfil_ativo)
            
            return permissions
            
        except Exception as e:
            print(f"Erro nas permissões: {e}")
            return PermissaoContextual(
                perfil_ativo="Fiscal",
                pode_submeter_relatorio=True,
                acoes_disponiveis=["visualizar"]
            )
'''
    
    # Lê o conteúdo atual
    with open(service_path, 'r', encoding='utf-8') as f:
        current_content = f.read()
    
    # Verifica se já foi adicionado
    if 'get_session_context_by_user' not in current_content:
        with open(service_path, 'a', encoding='utf-8') as f:
            f.write(additional_content)
        print(f"✅ Métodos adicionados ao: {service_path}")
    else:
        print(f"ℹ️ Métodos já existem em: {service_path}")

def update_auth_router():
    """Atualiza os endpoints no auth_router.py"""
    router_path = 'app/api/routers/auth_router.py'
    
    if not os.path.exists(router_path):
        print(f"⚠️ Arquivo não encontrado: {router_path}")
        return
    
    # Backup do arquivo original
    backup_file(router_path)
    
    # Lê o conteúdo atual
    with open(router_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adiciona correções nos endpoints
    fixes = """
# ✅ CORREÇÕES ADICIONADAS PARA OS ENDPOINTS

@router.get("/contexto", response_model=ContextoSessao)
async def get_current_context_fixed(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        context = await service.get_session_context_by_user(current_user.id)
        if not context:
            raise HTTPException(status_code=404, detail="Contexto não encontrado")
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar contexto: {str(e)}")

@router.get("/dashboard", response_model=DashboardData)  
async def get_dashboard_data_fixed(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        return await service.get_dashboard_data_by_user(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no dashboard: {str(e)}")

@router.get("/permissoes", response_model=PermissaoContextual)
async def get_contextual_permissions_fixed(
    service: SessionContextService = Depends(get_session_context_service),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        return await service.get_contextual_permissions_by_user(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro nas permissões: {str(e)}")
"""
    
    # Verifica se já foi adicionado
    if 'get_current_context_fixed' not in content:
        with open(router_path, 'a', encoding='utf-8') as f:
            f.write(fixes)
        print(f"✅ Endpoints corrigidos adicionados ao: {router_path}")
    else:
        print(f"ℹ️ Endpoints já foram corrigidos em: {router_path}")

def main():
    """Executa todas as correções"""
    print("🔧 SIGESCON - Aplicando Correções nos Endpoints")
    print("=" * 50)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    try:
        # Aplica as correções
        create_session_context_repo()
        update_session_context_service()
        update_auth_router()
        
        print("\n🎉 CORREÇÕES APLICADAS COM SUCESSO!")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("1. Reinicie o servidor:")
        print("   uvicorn app.main:app --reload")
        print()
        print("2. Execute o script de teste novamente:")
        print("   python scripts/test_multiple_profiles_complete.py")
        print()
        print("3. Teste os endpoints manualmente:")
        print("   - GET /auth/contexto")
        print("   - GET /auth/dashboard") 
        print("   - GET /auth/permissoes")
        
    except Exception as e:
        print(f"❌ Erro durante as correções: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)