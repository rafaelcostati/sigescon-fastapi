"""
Service para escalonamento de pendências vencidas
Envia notificações para gestores e administradores quando pendências não são resolvidas
"""
from typing import List, Dict, Any
from datetime import date, timedelta
import asyncpg

from app.repositories.config_repo import ConfigRepository
from app.repositories.pendencia_repo import PendenciaRepository
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services.email_service import EmailService


class EscalationService:
    """Service para gerenciar escalonamento de pendências"""

    def __init__(
        self,
        config_repo: ConfigRepository,
        pendencia_repo: PendenciaRepository,
        contrato_repo: ContratoRepository,
        usuario_repo: UsuarioRepository,
        email_service: EmailService
    ):
        self.config_repo = config_repo
        self.pendencia_repo = pendencia_repo
        self.contrato_repo = contrato_repo
        self.usuario_repo = usuario_repo
        self.email_service = email_service

    async def verificar_e_escalonar_pendencias(self) -> Dict[str, int]:
        """
        Verifica pendências vencidas e envia notificações de escalonamento

        Returns:
            Dicionário com contadores de emails enviados
        """
        print("🔔 Iniciando verificação de escalonamento de pendências...")

        # Verifica se o sistema está ativo
        config = await self.config_repo.get_escalonamento_config()

        if not config['ativo']:
            print("⏸️ Sistema de escalonamento desativado")
            return {
                'emails_gestor': 0,
                'emails_admin': 0,
                'total_pendencias_escalonadas': 0
            }

        dias_gestor = config['dias_gestor']
        dias_admin = config['dias_admin']

        print(f"⚙️ Configuração: Gestor={dias_gestor} dias, Admin={dias_admin} dias")

        # Buscar pendências vencidas não concluídas
        pendencias_vencidas = await self._buscar_pendencias_vencidas()

        if not pendencias_vencidas:
            print("✅ Nenhuma pendência vencida encontrada")
            return {
                'emails_gestor': 0,
                'emails_admin': 0,
                'total_pendencias_escalonadas': 0
            }

        print(f"📋 Encontradas {len(pendencias_vencidas)} pendências vencidas")

        # Separar pendências por nível de escalonamento
        pendencias_gestor = []
        pendencias_admin = []

        hoje = date.today()

        for pendencia in pendencias_vencidas:
            dias_vencida = (hoje - pendencia['data_vencimento']).days

            # Deve notificar admin?
            if dias_vencida >= dias_admin:
                pendencias_admin.append(pendencia)
            # Deve notificar gestor?
            elif dias_vencida >= dias_gestor:
                pendencias_gestor.append(pendencia)

        print(f"👥 Pendências para gestor: {len(pendencias_gestor)}")
        print(f"⚙️ Pendências para admin: {len(pendencias_admin)}")

        # Enviar notificações
        emails_gestor = await self._notificar_gestores(pendencias_gestor)
        emails_admin = await self._notificar_administradores(pendencias_admin)

        total_escalonadas = len(pendencias_gestor) + len(pendencias_admin)

        print(f"✅ Escalonamento concluído: {emails_gestor} emails para gestores, {emails_admin} emails para admins")

        return {
            'emails_gestor': emails_gestor,
            'emails_admin': emails_admin,
            'total_pendencias_escalonadas': total_escalonadas
        }

    async def _buscar_pendencias_vencidas(self) -> List[Dict[str, Any]]:
        """Busca pendências vencidas e não concluídas"""
        # Query para buscar pendências vencidas
        query = """
            SELECT
                p.id,
                p.titulo,
                p.descricao,
                p.data_vencimento,
                p.contrato_id,
                c.nr_contrato,
                c.objeto,
                c.gestor_id,
                c.fiscal_id,
                g.nome as gestor_nome,
                g.email as gestor_email,
                f.nome as fiscal_nome,
                f.email as fiscal_email
            FROM pendencia p
            INNER JOIN contrato c ON p.contrato_id = c.id
            INNER JOIN usuario g ON c.gestor_id = g.id
            INNER JOIN usuario f ON c.fiscal_id = f.id
            WHERE p.data_vencimento < CURRENT_DATE
            AND p.concluida = FALSE
            AND c.ativo = TRUE
            ORDER BY p.data_vencimento ASC
        """

        pendencias = await self.pendencia_repo.conn.fetch(query)
        return [dict(p) for p in pendencias]

    async def _notificar_gestores(self, pendencias: List[Dict[str, Any]]) -> int:
        """
        Envia emails de escalonamento para gestores

        Args:
            pendencias: Lista de pendências para escalonamento

        Returns:
            Número de emails enviados
        """
        if not pendencias:
            return 0

        # Agrupar pendências por gestor
        pendencias_por_gestor = {}
        for p in pendencias:
            gestor_id = p['gestor_id']
            if gestor_id not in pendencias_por_gestor:
                pendencias_por_gestor[gestor_id] = {
                    'nome': p['gestor_nome'],
                    'email': p['gestor_email'],
                    'pendencias': []
                }
            pendencias_por_gestor[gestor_id]['pendencias'].append(p)

        emails_enviados = 0

        # Enviar email para cada gestor
        for gestor_id, dados in pendencias_por_gestor.items():
            try:
                await self._enviar_email_escalonamento_gestor(
                    gestor_nome=dados['nome'],
                    gestor_email=dados['email'],
                    pendencias=dados['pendencias']
                )
                emails_enviados += 1
                print(f"📧 Email de escalonamento enviado para gestor: {dados['nome']}")
            except Exception as e:
                print(f"❌ Erro ao enviar email para gestor {dados['nome']}: {e}")

        return emails_enviados

    async def _notificar_administradores(self, pendencias: List[Dict[str, Any]]) -> int:
        """
        Envia emails de escalonamento para administradores

        Args:
            pendencias: Lista de pendências para escalonamento

        Returns:
            Número de emails enviados
        """
        if not pendencias:
            return 0

        # Buscar todos os administradores ativos
        query = """
            SELECT DISTINCT u.id, u.nome, u.email
            FROM usuario u
            INNER JOIN usuario_perfil up ON u.id = up.usuario_id
            INNER JOIN perfil p ON up.perfil_id = p.id
            WHERE p.nome = 'Administrador'
            AND u.ativo = TRUE
            AND u.data_exclusao IS NULL
        """

        admins = await self.usuario_repo.conn.fetch(query)

        if not admins:
            print("⚠️ Nenhum administrador encontrado para enviar escalonamento")
            return 0

        emails_enviados = 0

        # Enviar email para cada admin
        for admin in admins:
            try:
                await self._enviar_email_escalonamento_admin(
                    admin_nome=admin['nome'],
                    admin_email=admin['email'],
                    pendencias=pendencias
                )
                emails_enviados += 1
                print(f"📧 Email de escalonamento enviado para admin: {admin['nome']}")
            except Exception as e:
                print(f"❌ Erro ao enviar email para admin {admin['nome']}: {e}")

        return emails_enviados

    async def _enviar_email_escalonamento_gestor(
        self,
        gestor_nome: str,
        gestor_email: str,
        pendencias: List[Dict[str, Any]]
    ):
        """Envia email de escalonamento para gestor"""

        hoje = date.today()

        # Criar lista de pendências para o email
        lista_pendencias = ""
        for p in pendencias:
            dias_vencida = (hoje - p['data_vencimento']).days
            lista_pendencias += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                    <strong>{p['titulo']}</strong><br>
                    <span style="color: #6b7280; font-size: 14px;">Contrato #{p['nr_contrato']}</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {p['data_vencimento'].strftime('%d/%m/%Y')}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    <span style="background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-weight: 600;">
                        {dias_vencida} dias
                    </span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                    {p['fiscal_nome']}
                </td>
            </tr>
            """

        assunto = f"⚠️ ESCALONAMENTO: {len(pendencias)} Pendência(s) Vencida(s) Requer Atenção"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #f97316 0%, #dc2626 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">⚠️ Escalonamento de Pendências</h1>
                    <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Atenção necessária do Gestor</p>
                </div>

                <div style="background-color: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none;">
                    <p style="font-size: 16px; margin-top: 0;">Olá, <strong>{gestor_nome}</strong>,</p>

                    <p>Este email é uma <strong>notificação de escalonamento</strong>. As seguintes pendências sob sua gestão estão vencidas e ainda não foram resolvidas:</p>

                    <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <strong>📊 Total de pendências vencidas: {len(pendencias)}</strong>
                    </div>

                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background-color: #f9fafb;">
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Pendência / Contrato</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e5e7eb;">Vencimento</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e5e7eb;">Dias Vencida</th>
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Fiscal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {lista_pendencias}
                        </tbody>
                    </table>

                    <div style="background-color: #fef2f2; border: 1px solid #fecaca; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; color: #991b1b;"><strong>⏰ Ação Necessária</strong></p>
                        <p style="margin: 5px 0 0 0; color: #7f1d1d;">
                            Por favor, entre em contato com os fiscais responsáveis para verificar o andamento dessas pendências.
                        </p>
                    </div>

                    <p style="margin-top: 30px; font-size: 14px; color: #6b7280;">
                        Este é um email automático do sistema de gestão de contratos.<br>
                        Para mais informações, acesse o sistema SIGESCON.
                    </p>
                </div>

                <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280;">
                    SIGESCON - Sistema de Gestão de Contratos
                </div>
            </div>
        </body>
        </html>
        """

        await self.email_service.send_email(
            destinatario=gestor_email,
            assunto=assunto,
            corpo_html=corpo_html
        )

    async def _enviar_email_escalonamento_admin(
        self,
        admin_nome: str,
        admin_email: str,
        pendencias: List[Dict[str, Any]]
    ):
        """Envia email de escalonamento para administrador"""

        hoje = date.today()

        # Criar lista de pendências para o email
        lista_pendencias = ""
        for p in pendencias:
            dias_vencida = (hoje - p['data_vencimento']).days
            lista_pendencias += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                    <strong>{p['titulo']}</strong><br>
                    <span style="color: #6b7280; font-size: 14px;">Contrato #{p['nr_contrato']}</span><br>
                    <span style="color: #9ca3af; font-size: 12px;">{p['objeto'][:50]}...</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {p['data_vencimento'].strftime('%d/%m/%Y')}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    <span style="background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-weight: 600;">
                        {dias_vencida} dias
                    </span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                    <strong>Gestor:</strong> {p['gestor_nome']}<br>
                    <strong>Fiscal:</strong> {p['fiscal_nome']}
                </td>
            </tr>
            """

        assunto = f"🚨 ESCALONAMENTO CRÍTICO: {len(pendencias)} Pendência(s) com Prazo Excedido"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                    <h1 style="margin: 0; font-size: 26px;">🚨 Escalonamento Crítico</h1>
                    <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Intervenção Administrativa Necessária</p>
                </div>

                <div style="background-color: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none;">
                    <p style="font-size: 16px; margin-top: 0;">Olá, <strong>{admin_nome}</strong>,</p>

                    <p>Este email é uma <strong>notificação de escalonamento crítico</strong>. As seguintes pendências atingiram o prazo máximo de vencimento e requerem <strong>intervenção administrativa imediata</strong>:</p>

                    <div style="background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <strong style="color: #991b1b;">🚨 Total de pendências críticas: {len(pendencias)}</strong>
                    </div>

                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background-color: #f9fafb;">
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Pendência / Contrato</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e5e7eb;">Vencimento</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e5e7eb;">Dias Vencida</th>
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Responsáveis</th>
                            </tr>
                        </thead>
                        <tbody>
                            {lista_pendencias}
                        </tbody>
                    </table>

                    <div style="background-color: #fef2f2; border: 2px solid #dc2626; padding: 20px; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; color: #991b1b; font-size: 16px;"><strong>⚠️ Ação Urgente Necessária</strong></p>
                        <p style="margin: 10px 0 0 0; color: #7f1d1d;">
                            Estas pendências já foram escalonadas para os gestores, mas continuam sem resolução.<br>
                            Recomenda-se contato direto com os gestores e fiscais para regularização imediata.
                        </p>
                    </div>

                    <p style="margin-top: 30px; font-size: 14px; color: #6b7280;">
                        Este é um email automático do sistema de gestão de contratos.<br>
                        Para mais informações e ações corretivas, acesse o sistema SIGESCON.
                    </p>
                </div>

                <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280;">
                    SIGESCON - Sistema de Gestão de Contratos
                </div>
            </div>
        </body>
        </html>
        """

        await self.email_service.send_email(
            destinatario=admin_email,
            assunto=assunto,
            corpo_html=corpo_html
        )
