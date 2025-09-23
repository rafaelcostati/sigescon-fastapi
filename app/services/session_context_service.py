# app/services/session_context_service.py
import uuid
from typing import Optional, List, Dict
from fastapi import HTTPException, status

from app.repositories.session_context_repo import SessionContextRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository
from app.repositories.contrato_repo import ContratoRepository
from app.schemas.session_context_schema import (
    ContextoSessao, PerfilAtivo, AlternarPerfilRequest, 
    LoginResponse, DashboardData, PermissaoContextual,
    PerfilSwitchHistoryItem
)

class SessionContextService:
    def __init__(self, 
                 session_repo: SessionContextRepository,
                 usuario_repo: UsuarioRepository,
                 usuario_perfil_repo: UsuarioPerfilRepository,
                 contrato_repo: ContratoRepository):
        self.session_repo = session_repo
        self.usuario_repo = usuario_repo
        self.usuario_perfil_repo = usuario_perfil_repo
        self.contrato_repo = contrato_repo

    async def create_session_context(self, usuario_id: int, 
                                   perfil_inicial_id: Optional[int] = None,
                                   ip_address: Optional[str] = None,
                                   user_agent: Optional[str] = None) -> ContextoSessao:
        """Cria contexto de sessão para um usuário"""
        
        # Busca perfis disponíveis do usuário
        perfis_disponiveis = await self.session_repo.get_user_available_profiles(usuario_id)


        if not perfis_disponiveis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não possui perfis ativos no sistema"
            )
        
        # Define perfil inicial
        if perfil_inicial_id:
            # Valida se o usuário pode usar este perfil
            if not await self.session_repo.validate_profile_for_user(usuario_id, perfil_inicial_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuário não tem permissão para usar este perfil"
                )
            perfil_ativo_id = perfil_inicial_id
        else:
            # Usa o primeiro perfil disponível (por ordem de prioridade)
            perfil_ativo_id = perfis_disponiveis[0]['id']
        
        # Gera ID único para a sessão
        sessao_id = str(uuid.uuid4())
        
        # Cria contexto no banco
        await self.session_repo.create_session_context(
            usuario_id=usuario_id,
            sessao_id=sessao_id,
            perfil_ativo_id=perfil_ativo_id,
            perfis_disponiveis=perfis_disponiveis,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Busca nome do perfil ativo
        perfil_ativo_nome = next(p['nome'] for p in perfis_disponiveis if p['id'] == perfil_ativo_id)
        
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
            perfil_ativo_id=perfil_ativo_id,
            perfil_ativo_nome=perfil_ativo_nome,
            perfis_disponiveis=perfis_ativos,
            pode_alternar=len(perfis_disponiveis) > 1,
            sessao_id=sessao_id
        )

    async def get_session_context(self, sessao_id: str) -> Optional[ContextoSessao]:
        """Busca contexto de sessão existente"""
        context_data = await self.session_repo.get_session_context(sessao_id)

        if not context_data:
            return None


        # Atualiza última atividade
        await self.session_repo.update_last_activity(sessao_id)

        # Busca perfis disponíveis atualizados
        perfis_disponiveis = await self.session_repo.get_user_available_profiles(
            context_data['usuario_id']
        )
        
        perfis_ativos = [
            PerfilAtivo(
                id=p['id'],
                nome=p['nome'],
                descricao=p.get('descricao'),
                pode_ser_selecionado=True
            ) for p in perfis_disponiveis
        ]
        
        return ContextoSessao(
            usuario_id=context_data['usuario_id'],
            perfil_ativo_id=context_data['perfil_ativo_id'],
            perfil_ativo_nome=context_data['perfil_ativo_nome'],
            perfis_disponiveis=perfis_ativos,
            pode_alternar=len(perfis_disponiveis) > 1,
            sessao_id=sessao_id,
            data_ultima_alternancia=context_data.get('data_ultima_alternancia')
        )

    async def switch_profile(self, sessao_id: str, request: AlternarPerfilRequest,
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> ContextoSessao:
        """Alterna perfil ativo na sessão"""
        
        # Busca contexto atual
        current_context = await self.get_session_context(sessao_id)
        if not current_context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sessão não encontrada"
            )
        
        # Valida se o novo perfil está disponível
        perfil_disponivel = next(
            (p for p in current_context.perfis_disponiveis if p.id == request.novo_perfil_id),
            None
        )
        
        if not perfil_disponivel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil não disponível para este usuário"
            )
        
        # Não faz nada se já está no perfil solicitado
        if current_context.perfil_ativo_id == request.novo_perfil_id:
            return current_context
        
        # Atualiza no banco
        success = await self.session_repo.update_active_profile(
            sessao_id=sessao_id,
            novo_perfil_id=request.novo_perfil_id,
            justificativa=request.justificativa,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao alternar perfil"
            )
        
        # Retorna contexto atualizado
        return await self.get_session_context(sessao_id)

    async def switch_profile_context(self, sessao_id: str, usuario_id: int,
                                   novo_perfil_id: int, justificativa: str,
                                   ip_address: Optional[str] = None,
                                   user_agent: Optional[str] = None) -> ContextoSessao:
        """Método específico para alternância de perfil via endpoint"""

        print(f"🔧 DEBUG: switch_profile_context chamado - usuário {usuario_id}, perfil {novo_perfil_id}")

        # REMOVIDA a validação duplicada - já foi feita no switch_profile
        # A validação já aconteceu na verificação dos perfis disponíveis

        # Atualiza no banco
        success = await self.session_repo.update_active_profile(
            sessao_id=sessao_id,
            novo_perfil_id=novo_perfil_id,
            justificativa=justificativa,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao alternar perfil"
            )

        # Retorna contexto atualizado
        return await self.get_session_context(sessao_id)

    async def get_session_context_by_user(self, usuario_id: int) -> Optional[ContextoSessao]:
        """Busca contexto de sessão ativo do usuário"""
        session_data = await self.session_repo.get_active_session_by_user(usuario_id)

        if not session_data:
            return None

        return await self.get_session_context(session_data['sessao_id'])

    async def get_dashboard_data(self, sessao_id: str) -> DashboardData:
        """Retorna dados do dashboard baseados no perfil ativo"""
        context = await self.get_session_context(sessao_id)
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sessão não encontrada"
            )
        
        perfil_ativo = context.perfil_ativo_nome
        
        # Define widgets e menus baseados no perfil
        if perfil_ativo == "Administrador":
            widgets = ["contratos_total", "usuarios_ativos", "relatorios_pendentes", "estatisticas_sistema"]
            menus = [
                {"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
                {"nome": "Contratos", "icon": "contracts", "route": "/contratos"},
                {"nome": "Usuários", "icon": "users", "route": "/usuarios"},
                {"nome": "Relatórios", "icon": "reports", "route": "/relatorios"},
                {"nome": "Configurações", "icon": "settings", "route": "/configuracoes"}
            ]
            permissoes = ["criar_contrato", "editar_contrato", "gerenciar_usuarios", "aprovar_relatorios"]
            
        elif perfil_ativo == "Gestor":
            widgets = ["meus_contratos", "relatorios_equipe", "pendencias_gestao"]
            menus = [
                {"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
                {"nome": "Meus Contratos", "icon": "contracts", "route": "/contratos/gestao"},
                {"nome": "Relatórios", "icon": "reports", "route": "/relatorios/gestao"},
                {"nome": "Equipe", "icon": "team", "route": "/equipe"}
            ]
            permissoes = ["ver_contratos_gestao", "aprovar_relatorios", "criar_pendencias"]
            
        elif perfil_ativo == "Fiscal":
            widgets = ["meus_contratos_fiscalizacao", "pendencias_ativas", "relatorios_submetidos"]
            menus = [
                {"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
                {"nome": "Fiscalização", "icon": "audit", "route": "/contratos/fiscalizacao"},
                {"nome": "Pendências", "icon": "tasks", "route": "/pendencias"},
                {"nome": "Relatórios", "icon": "reports", "route": "/relatorios/fiscal"}
            ]
            permissoes = ["submeter_relatorios", "ver_contratos_fiscal", "responder_pendencias"]
            
        else:
            widgets = []
            menus = []
            permissoes = []
        
        # Busca estatísticas básicas
        estatisticas = await self._get_profile_statistics(context.usuario_id, perfil_ativo)
        
        return DashboardData(
            perfil_ativo=perfil_ativo,
            widgets_disponiveis=widgets,
            menus_disponiveis=menus,
            permissoes_ativas=permissoes,
            estatisticas=estatisticas
        )

    async def get_contextual_permissions(self, sessao_id: str) -> PermissaoContextual:
        """Retorna permissões baseadas no contexto atual"""
        context = await self.get_session_context(sessao_id)
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sessão não encontrada"
            )
        
        perfil_ativo = context.perfil_ativo_nome
        usuario_id = context.usuario_id
        
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
                acoes_disponiveis=["criar", "editar", "deletar", "aprovar", "rejeitar", "gerenciar"]
            )
            
        elif perfil_ativo == "Gestor":
            # Busca contratos onde é gestor
            contratos_gestao, _ = await self.contrato_repo.get_all_contratos(
                filters={'gestor_id': usuario_id}, limit=1000, offset=0
            )
            contratos_ids = [c['id'] for c in contratos_gestao]
            
            permissions = PermissaoContextual(
                perfil_ativo=perfil_ativo,
                pode_criar_contrato=False,
                pode_editar_contrato=False,
                pode_criar_pendencia=True,
                pode_submeter_relatorio=False,
                pode_aprovar_relatorio=True,
                pode_gerenciar_usuarios=False,
                pode_ver_todos_contratos=False,
                contratos_visiveis=contratos_ids,
                acoes_disponiveis=["visualizar", "criar_pendencia", "aprovar_relatorio"]
            )
            
        elif perfil_ativo == "Fiscal":
            # Busca contratos onde é fiscal
            contratos_fiscal, _ = await self.contrato_repo.get_all_contratos(
                filters={'fiscal_id': usuario_id}, limit=1000, offset=0
            )
            contratos_ids = [c['id'] for c in contratos_fiscal]
            
            permissions = PermissaoContextual(
                perfil_ativo=perfil_ativo,
                pode_criar_contrato=False,
                pode_editar_contrato=False,
                pode_criar_pendencia=False,
                pode_submeter_relatorio=True,
                pode_aprovar_relatorio=False,
                pode_gerenciar_usuarios=False,
                pode_ver_todos_contratos=False,
                contratos_visiveis=contratos_ids,
                acoes_disponiveis=["visualizar", "submeter_relatorio", "responder_pendencia"]
            )
            
        else:
            permissions = PermissaoContextual(perfil_ativo=perfil_ativo)
        
        return permissions

    async def get_profile_switch_history(self, usuario_id: int) -> List[PerfilSwitchHistoryItem]:
        """Busca histórico de alternância de perfis"""
        history_data = await self.session_repo.get_profile_switch_history(usuario_id)
        return [PerfilSwitchHistoryItem.model_validate(h) for h in history_data]

    async def logout_session(self, sessao_id: str) -> bool:
        """Finaliza uma sessão"""
        return await self.session_repo.deactivate_session(sessao_id)

    async def cleanup_expired_sessions(self) -> int:
        """Remove sessões expiradas"""
        return await self.session_repo.cleanup_expired_sessions(hours=24)

    async def _get_profile_statistics(self, usuario_id: int, perfil_ativo: str) -> Dict:
        """Busca estatísticas específicas do perfil"""
        stats = {}
        
        if perfil_ativo == "Administrador":
            stats = {
                "total_contratos": await self._count_total_contracts(),
                "usuarios_ativos": await self._count_active_users(),
                "relatorios_pendentes": await self._count_pending_reports(),
                "pendencias_abertas": await self._count_open_tasks()
            }
        elif perfil_ativo == "Gestor":
            stats = {
                "contratos_sob_gestao": await self._count_user_managed_contracts(usuario_id),
                "relatorios_para_aprovar": await self._count_reports_to_approve(usuario_id),
                "pendencias_criadas": await self._count_created_tasks(usuario_id)
            }
        elif perfil_ativo == "Fiscal":
            stats = {
                "contratos_fiscalizados": await self._count_user_fiscal_contracts(usuario_id),
                "pendencias_ativas": await self._count_user_active_tasks(usuario_id),
                "relatorios_submetidos": await self._count_user_submitted_reports(usuario_id)
            }
        
        return stats

    # Métodos auxiliares para estatísticas
    async def _count_total_contracts(self) -> int:
        return await self.session_repo.conn.fetchval("SELECT COUNT(*) FROM contrato WHERE ativo = TRUE")

    async def _count_active_users(self) -> int:
        return await self.session_repo.conn.fetchval("SELECT COUNT(*) FROM usuario WHERE ativo = TRUE")

    async def _count_pending_reports(self) -> int:
        return await self.session_repo.conn.fetchval("""
            SELECT COUNT(*) FROM relatoriofiscal rf
            JOIN statusrelatorio sr ON rf.status_id = sr.id
            WHERE sr.nome = 'Pendente de Análise'
        """)

    async def _count_open_tasks(self) -> int:
        return await self.session_repo.conn.fetchval("""
            SELECT COUNT(*) FROM pendenciarelatorio pr
            JOIN statuspendencia sp ON pr.status_pendencia_id = sp.id
            WHERE sp.nome = 'Pendente'
        """)

    async def _count_user_managed_contracts(self, usuario_id: int) -> int:
        return await self.session_repo.conn.fetchval("""
            SELECT COUNT(*) FROM contrato 
            WHERE gestor_id = $1 AND ativo = TRUE
        """, usuario_id)

    async def _count_reports_to_approve(self, usuario_id: int) -> int:
        return await self.session_repo.conn.fetchval("""
            SELECT COUNT(*) FROM relatoriofiscal rf
            JOIN contrato c ON rf.contrato_id = c.id
            JOIN statusrelatorio sr ON rf.status_id = sr.id
            WHERE c.gestor_id = $1 AND sr.nome = 'Pendente de Análise'
        """, usuario_id)

    async def _count_created_tasks(self, usuario_id: int) -> int:
        return await self.session_repo.conn.fetchval("""
            SELECT COUNT(*) FROM pendenciarelatorio 
            WHERE criado_por_usuario_id = $1
        """, usuario_id)

    async def _count_user_fiscal_contracts(self, usuario_id: int) -> int:
        return await self.session_repo.conn.fetchval("""
            SELECT COUNT(*) FROM contrato 
            WHERE (fiscal_id = $1 OR fiscal_substituto_id = $1) AND ativo = TRUE
        """, usuario_id)

    async def _count_user_active_tasks(self, usuario_id: int) -> int:
        return await self.session_repo.conn.fetchval("""
            SELECT COUNT(*) FROM pendenciarelatorio pr
            JOIN contrato c ON pr.contrato_id = c.id
            JOIN statuspendencia sp ON pr.status_pendencia_id = sp.id
            WHERE (c.fiscal_id = $1 OR c.fiscal_substituto_id = $1) 
            AND sp.nome = 'Pendente'
        """, usuario_id)

    async def _count_user_submitted_reports(self, usuario_id: int) -> int:
        return await self.session_repo.conn.fetchval("""
            SELECT COUNT(*) FROM relatoriofiscal 
            WHERE fiscal_usuario_id = $1
        """, usuario_id)

    async def get_session_context_by_user(self, usuario_id: int) -> Optional[ContextoSessao]:
        """Busca contexto de sessão ativo baseado no ID do usuário"""
        try:
            # Primeiro tenta buscar sessão ativa existente
            session_data = await self.session_repo.get_active_session_by_user(usuario_id)

            if session_data and session_data.get('sessao_id'):
                # Se existe sessão ativa, busca o contexto completo
                return await self.get_session_context(session_data['sessao_id'])

            # Senão, busca perfis disponíveis para criar contexto temporário
            perfis_disponiveis = await self.session_repo.get_user_available_profiles(usuario_id)

            if not perfis_disponiveis:
                return None

            # Usa o primeiro perfil como ativo (ordenado por prioridade)
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

    async def get_dashboard_data(self, usuario_id: int) -> DashboardData:
        """ Retorna dados do dashboard baseados no usuário"""
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
                widgets = ["contratos_total", "usuarios_ativos", "relatorios_pendentes", "estatisticas_sistema"]
                menus = [
                    {"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
                    {"nome": "Contratos", "icon": "contracts", "route": "/contratos"},
                    {"nome": "Usuários", "icon": "users", "route": "/usuarios"},
                    {"nome": "Relatórios", "icon": "reports", "route": "/relatorios"},
                    {"nome": "Configurações", "icon": "settings", "route": "/configuracoes"}
                ]
                permissoes = ["criar_contrato", "editar_contrato", "gerenciar_usuarios", "aprovar_relatorios"]
                
            elif perfil_ativo == "Gestor":
                widgets = ["meus_contratos", "relatorios_equipe", "pendencias_gestao"]
                menus = [
                    {"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
                    {"nome": "Meus Contratos", "icon": "contracts", "route": "/contratos/gestao"},
                    {"nome": "Relatórios", "icon": "reports", "route": "/relatorios/gestao"},
                    {"nome": "Equipe", "icon": "team", "route": "/equipe"}
                ]
                permissoes = ["ver_contratos_gestao", "aprovar_relatorios", "criar_pendencias"]
                
            elif perfil_ativo == "Fiscal":
                widgets = ["meus_contratos_fiscalizacao", "pendencias_ativas", "relatorios_submetidos"]
                menus = [
                    {"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
                    {"nome": "Fiscalização", "icon": "audit", "route": "/contratos/fiscalizacao"},
                    {"nome": "Pendências", "icon": "tasks", "route": "/pendencias"},
                    {"nome": "Relatórios", "icon": "reports", "route": "/relatorios/fiscal"}
                ]
                permissoes = ["submeter_relatorios", "ver_contratos_fiscal", "responder_pendencias"]
                
            else:
                widgets = []
                menus = []
                permissoes = []
            
            # Busca estatísticas básicas
            estatisticas = await self._get_profile_statistics(usuario_id, perfil_ativo)
            
            return DashboardData(
                perfil_ativo=perfil_ativo,
                widgets_disponiveis=widgets,
                menus_disponiveis=menus,
                permissoes_ativas=permissoes,
                estatisticas=estatisticas
            )
            
        except Exception as e:
            print(f"Erro no dashboard: {e}")
            # Retorna dashboard básico em caso de erro
            return DashboardData(
                perfil_ativo="Fiscal",
                widgets_disponiveis=["básico"],
                menus_disponiveis=[{"nome": "Dashboard", "icon": "dashboard", "route": "/dashboard"}],
                permissoes_ativas=["visualizar"],
                estatisticas={"total": 0}
            )

    async def get_contextual_permissions(self, usuario_id: int) -> PermissaoContextual:
        
        try:
            # Busca perfis do usuário
            perfis = await self.usuario_perfil_repo.get_user_profiles(usuario_id)
            
            if not perfis:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuário não possui perfis ativos"
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
                    acoes_disponiveis=["criar", "editar", "deletar", "aprovar", "rejeitar", "gerenciar"]
                )
                
            elif perfil_ativo == "Gestor":
                # Busca contratos onde é gestor
                try:
                    contratos_gestao, _ = await self.contrato_repo.get_all_contratos(
                        filters={'gestor_id': usuario_id}, limit=100, offset=0
                    )
                    contratos_ids = [c['id'] for c in contratos_gestao]
                except:
                    contratos_ids = []
                
                permissions = PermissaoContextual(
                    perfil_ativo=perfil_ativo,
                    pode_criar_contrato=False,
                    pode_editar_contrato=False,
                    pode_criar_pendencia=True,
                    pode_submeter_relatorio=False,
                    pode_aprovar_relatorio=True,
                    pode_gerenciar_usuarios=False,
                    pode_ver_todos_contratos=False,
                    contratos_visiveis=contratos_ids,
                    acoes_disponiveis=["visualizar", "criar_pendencia", "aprovar_relatorio"]
                )
                
            elif perfil_ativo == "Fiscal":
                # Busca contratos onde é fiscal
                try:
                    contratos_fiscal, _ = await self.contrato_repo.get_all_contratos(
                        filters={'fiscal_id': usuario_id}, limit=100, offset=0
                    )
                    contratos_ids = [c['id'] for c in contratos_fiscal]
                except:
                    contratos_ids = []
                
                permissions = PermissaoContextual(
                    perfil_ativo=perfil_ativo,
                    pode_criar_contrato=False,
                    pode_editar_contrato=False,
                    pode_criar_pendencia=False,
                    pode_submeter_relatorio=True,
                    pode_aprovar_relatorio=False,
                    pode_gerenciar_usuarios=False,
                    pode_ver_todos_contratos=False,
                    contratos_visiveis=contratos_ids,
                    acoes_disponiveis=["visualizar", "submeter_relatorio", "responder_pendencia"]
                )
                
            else:
                permissions = PermissaoContextual(perfil_ativo=perfil_ativo)
            
            return permissions
            
        except Exception as e:
            print(f"Erro nas permissões: {e}")
            # Retorna permissões básicas em caso de erro
            return PermissaoContextual(
                perfil_ativo="Fiscal",
                pode_submeter_relatorio=True,
                acoes_disponiveis=["visualizar"]
            )