# app/services/pendencia_service.py
from typing import List, Optional
from fastapi import HTTPException, status, Request
import logging

# Repositórios
from app.repositories.pendencia_repo import PendenciaRepository
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.status_pendencia_repo import StatusPendenciaRepository

# Schemas
from app.schemas.pendencia_schema import Pendencia, PendenciaCreate
from app.schemas.usuario_schema import Usuario

# Services
from app.services.email_service import EmailService
from app.services.audit_integration import (
    audit_criar_pendencia,
    audit_atualizar_pendencia
)

logger = logging.getLogger(__name__)

class PendenciaService:
    def __init__(self,
                 pendencia_repo: PendenciaRepository,
                 contrato_repo: ContratoRepository,
                 usuario_repo: UsuarioRepository,
                 status_pendencia_repo: StatusPendenciaRepository):
        self.pendencia_repo = pendencia_repo
        self.contrato_repo = contrato_repo
        self.usuario_repo = usuario_repo
        self.status_pendencia_repo = status_pendencia_repo

    async def _validate_foreign_keys(self, pendencia: PendenciaCreate, contrato_id: int):
        """Valida se todas as chaves estrangeiras existem"""
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
        
        if not await self.usuario_repo.get_user_by_id(pendencia.criado_por_usuario_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário criador não encontrado")

        if not await self.status_pendencia_repo.get_by_id(pendencia.status_pendencia_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de pendência não encontrado")

    async def create_pendencia(
        self,
        contrato_id: int,
        pendencia_create: PendenciaCreate,
        current_user: Optional[Usuario] = None,
        request: Optional[Request] = None
    ) -> Pendencia:
        """Cria uma nova pendência e envia notificação por email para o fiscal e fiscal substituto"""
        await self._validate_foreign_keys(pendencia_create, contrato_id)

        # Cria a pendência no banco de dados
        new_pendencia_data = await self.pendencia_repo.create_pendencia(contrato_id, pendencia_create)

        # Busca dados do contrato para o log de auditoria
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)

        # Log de auditoria
        if current_user and contrato:
            try:
                await audit_criar_pendencia(
                    conn=self.pendencia_repo.conn,
                    request=request,
                    usuario=current_user,
                    pendencia_id=new_pendencia_data['id'],
                    titulo_pendencia=pendencia_create.titulo,
                    contrato_nr=contrato['nr_contrato'],
                    perfil_usado=current_user.perfil_ativo if hasattr(current_user, 'perfil_ativo') else None
                )
            except Exception as e:
                logger.warning(f"Erro ao criar log de auditoria para pendência {new_pendencia_data['id']}: {e}")

        # === NOTIFICAÇÃO POR EMAIL COM TEMPLATES ===
        try:
            if contrato:
                from app.services.email_templates import EmailTemplates

                # Enviar email para o fiscal principal
                if contrato.get('fiscal_id'):
                    fiscal = await self.usuario_repo.get_user_by_id(contrato['fiscal_id'])
                    if fiscal:
                        subject, body = EmailTemplates.pending_report_notification(
                            fiscal_nome=fiscal['nome'],
                            contrato_data=contrato,
                            pendencia_data=new_pendencia_data
                        )
                        await EmailService.send_email(fiscal['email'], subject, body, is_html=True)
                        print(f"✅ Email de pendência enviado para o fiscal principal: {fiscal['email']}")

                # Enviar email para o fiscal substituto (se houver)
                if contrato.get('fiscal_substituto_id'):
                    fiscal_substituto = await self.usuario_repo.get_user_by_id(contrato['fiscal_substituto_id'])
                    if fiscal_substituto:
                        subject, body = EmailTemplates.pending_report_notification(
                            fiscal_nome=fiscal_substituto['nome'],
                            contrato_data=contrato,
                            pendencia_data=new_pendencia_data
                        )
                        await EmailService.send_email(fiscal_substituto['email'], subject, body, is_html=True)
                        print(f"✅ Email de pendência enviado para o fiscal substituto: {fiscal_substituto['email']}")
        except Exception as e:
            # Log do erro, mas não falha a criação da pendência
            print(f"❌ Erro ao enviar email de notificação da pendência {new_pendencia_data['id']}: {e}")

        return Pendencia.model_validate(new_pendencia_data)

    async def get_pendencias_by_contrato_id(self, contrato_id: int) -> List[Pendencia]:
        """Lista todas as pendências de um contrato específico"""
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
            
        pendencias_data = await self.pendencia_repo.get_pendencias_by_contrato_id(contrato_id)
        return [Pendencia.model_validate(p) for p in pendencias_data]

    async def get_pendencia_by_id(self, pendencia_id: int) -> Pendencia:
        """Busca uma pendência específica pelo ID"""
        pendencia_data = await self.pendencia_repo.get_pendencia_by_id(pendencia_id)
        if not pendencia_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pendência não encontrada")
        
        return Pendencia.model_validate(pendencia_data)

    async def update_pendencia_status(
        self,
        pendencia_id: int,
        novo_status_id: int,
        current_user: Optional[Usuario] = None,
        request: Optional[Request] = None
    ) -> Pendencia:
        """Atualiza o status de uma pendência"""
        # Verifica se a pendência existe
        pendencia_antiga = await self.pendencia_repo.get_pendencia_by_id(pendencia_id)
        if not pendencia_antiga:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pendência não encontrada")

        # Verifica se o status existe
        novo_status = await self.status_pendencia_repo.get_by_id(novo_status_id)
        if not novo_status:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de pendência não encontrado")

        # Busca status antigo
        status_antigo = await self.status_pendencia_repo.get_by_id(pendencia_antiga['status_pendencia_id'])

        # Atualiza o status
        await self.pendencia_repo.update_pendencia_status(pendencia_id, novo_status_id)

        # Log de auditoria
        if current_user:
            try:
                await audit_atualizar_pendencia(
                    conn=self.pendencia_repo.conn,
                    request=request,
                    usuario=current_user,
                    pendencia_id=pendencia_id,
                    titulo_pendencia=pendencia_antiga['titulo'],
                    status_anterior=status_antigo['nome'] if status_antigo else None,
                    status_novo=novo_status['nome'],
                    perfil_usado=current_user.perfil_ativo if hasattr(current_user, 'perfil_ativo') else None
                )
            except Exception as e:
                logger.warning(f"Erro ao criar log de auditoria para pendência {pendencia_id}: {e}")

        # Retorna a pendência atualizada
        return await self.get_pendencia_by_id(pendencia_id)

    async def get_pendencias_vencendo(self, dias_antecedencia: int = 7) -> List[Pendencia]:
        """Busca pendências que estão vencendo nos próximos X dias"""
        from datetime import date, timedelta
        
        data_limite = date.today() + timedelta(days=dias_antecedencia)
        
        # Busca pendências que vencem até a data limite
        pendencias_due = await self.pendencia_repo.get_due_pendencias()
        
        pendencias_vencendo = []
        for pendencia_data in pendencias_due:
            if pendencia_data['data_prazo'] <= data_limite:
                pendencias_vencendo.append(Pendencia.model_validate(pendencia_data))
        
        return pendencias_vencendo

    async def send_deadline_reminders(self) -> int:
        """
        Envia lembretes de prazo para pendências que estão vencendo.
        Retorna o número de emails enviados.
        """
        from datetime import date
        
        emails_enviados = 0
        
        try:
            # Busca todas as pendências com status 'Pendente'
            pendencias_due = await self.pendencia_repo.get_due_pendencias()
            
            today = date.today()
            
            for pendencia_data in pendencias_due:
                prazo = pendencia_data['data_prazo']
                if isinstance(prazo, str):
                    from datetime import datetime
                    prazo = datetime.strptime(prazo, '%Y-%m-%d').date()
                
                dias_restantes = (prazo - today).days
                
                # Envia lembrete em intervalos específicos: 15, 7, 3, 1, 0 dias
                if dias_restantes in [15, 7, 3, 1, 0]:
                    try:
                        # Busca dados completos do contrato para o template
                        contrato = await self.contrato_repo.find_contrato_by_id(pendencia_data['contrato_id'])

                        if contrato:
                            from app.services.email_templates import EmailTemplates

                            # Enviar lembrete para o fiscal principal
                            subject, body = EmailTemplates.pending_report_notification(
                                fiscal_nome=pendencia_data['fiscal_nome'],
                                contrato_data=contrato,
                                pendencia_data=pendencia_data
                            )

                            await EmailService.send_email(pendencia_data['fiscal_email'], subject, body)
                            emails_enviados += 1

                            print(f"✅ Lembrete enviado para o fiscal principal {pendencia_data['fiscal_nome']} - {dias_restantes} dias restantes")

                            # Enviar lembrete para o fiscal substituto (se houver)
                            if contrato.get('fiscal_substituto_id'):
                                fiscal_substituto = await self.usuario_repo.get_user_by_id(contrato['fiscal_substituto_id'])
                                if fiscal_substituto:
                                    subject_sub, body_sub = EmailTemplates.pending_report_notification(
                                        fiscal_nome=fiscal_substituto['nome'],
                                        contrato_data=contrato,
                                        pendencia_data=pendencia_data
                                    )

                                    await EmailService.send_email(fiscal_substituto['email'], subject_sub, body_sub)
                                    emails_enviados += 1

                                    print(f"✅ Lembrete enviado para o fiscal substituto {fiscal_substituto['nome']} - {dias_restantes} dias restantes")

                    except Exception as e:
                        print(f"❌ Erro ao enviar lembrete para pendência {pendencia_data['id']}: {e}")
            
            print(f"📧 Total de lembretes enviados: {emails_enviados}")
            return emails_enviados
            
        except Exception as e:
            print(f"❌ Erro geral ao enviar lembretes de prazo: {e}")
            return 0

    async def get_pendencias_by_fiscal(self, fiscal_id: int) -> List[Pendencia]:
        """Busca todas as pendências atribuídas a um fiscal específico"""
        # Verifica se o fiscal existe
        if not await self.usuario_repo.get_user_by_id(fiscal_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal não encontrado")
        
        # Busca contratos onde o usuário é fiscal
        contratos_data, _ = await self.contrato_repo.get_all_contratos(
            filters={'fiscal_id': fiscal_id},
            limit=1000,  # Limite alto para pegar todos
            offset=0
        )
        
        pendencias_fiscal = []
        for contrato in contratos_data:
            pendencias_contrato = await self.get_pendencias_by_contrato_id(contrato['id'])
            pendencias_fiscal.extend(pendencias_contrato)
        
        return pendencias_fiscal

    async def cancelar_pendencia(self, contrato_id: int, pendencia_id: int, admin_usuario_id: int) -> Pendencia:
        """
        Cancela uma pendência e notifica o fiscal por email.

        Regras de negócio:
        - Só pode cancelar se a pendência estiver com status 'Pendente' (sem relatório enviado)
        - Não pode cancelar se já há relatório 'Pendente de Análise'
        - Só pode cancelar após rejeição se o relatório foi rejeitado
        """
        # Verifica se o contrato existe
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if not contrato:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")

        # Verifica se a pendência existe e pertence ao contrato
        pendencia = await self.pendencia_repo.get_pendencia_by_id(pendencia_id)
        if not pendencia or pendencia['contrato_id'] != contrato_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pendência não encontrada para este contrato")

        # === VALIDAÇÕES DAS REGRAS DE NEGÓCIO ===

        # Verifica se há relatório vinculado a esta pendência que esteja sob análise
        from app.repositories.relatorio_repo import RelatorioRepository
        relatorio_repo = RelatorioRepository(self.pendencia_repo.conn)

        # Busca relatórios desta pendência
        relatorios_pendencia = await relatorio_repo.get_relatorios_by_pendencia_id(pendencia_id)

        # Verifica se há relatório 'Pendente de Análise'
        relatorio_sob_analise = next(
            (r for r in relatorios_pendencia if r.get('status_nome') == 'Pendente de Análise'),
            None
        )

        if relatorio_sob_analise:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível cancelar pendência com relatório sob análise. Analise o relatório primeiro (aprovar/rejeitar)."
            )

        # Verifica se a pendência está em status que permite cancelamento
        status_atual = pendencia.get('status_nome', '')

        # Pode cancelar se:
        # 1. Status é 'Pendente' (fiscal ainda não enviou relatório)
        # 2. Status é 'Pendente' após uma rejeição (fiscal pode reenviar, mas admin pode cancelar)
        if status_atual not in ['Pendente']:
            if status_atual == 'Concluída':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Não é possível cancelar pendência já concluída."
                )
            elif status_atual == 'Cancelada':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Esta pendência já foi cancelada."
                )
            elif status_atual == 'Aguardando Análise':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Não é possível cancelar pendência com relatório aguardando análise. Analise o relatório primeiro."
                )

        # Busca o status 'Cancelada'
        all_status = await self.status_pendencia_repo.get_all()
        status_cancelada = next((s for s in all_status if s['nome'] == 'Cancelada'), None)

        if not status_cancelada:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Status 'Cancelada' não encontrado no sistema"
            )

        # Atualiza o status da pendência
        await self.pendencia_repo.update_pendencia_status(pendencia_id, status_cancelada['id'])

        # === NOTIFICAÇÃO POR EMAIL DE CANCELAMENTO ===
        try:
            from app.services.email_templates import EmailTemplates

            # Enviar email para o fiscal principal
            if contrato.get('fiscal_id'):
                fiscal = await self.usuario_repo.get_user_by_id(contrato['fiscal_id'])
                if fiscal:
                    subject, body = EmailTemplates.pending_cancellation_notification(
                        fiscal_nome=fiscal['nome'],
                        contrato_data=contrato,
                        pendencia_data=pendencia
                    )
                    await EmailService.send_email(fiscal['email'], subject, body, is_html=True)
                    print(f"✅ Email de cancelamento de pendência enviado para o fiscal principal: {fiscal['email']}")

            # Enviar email para o fiscal substituto (se houver)
            if contrato.get('fiscal_substituto_id'):
                fiscal_substituto = await self.usuario_repo.get_user_by_id(contrato['fiscal_substituto_id'])
                if fiscal_substituto:
                    subject, body = EmailTemplates.pending_cancellation_notification(
                        fiscal_nome=fiscal_substituto['nome'],
                        contrato_data=contrato,
                        pendencia_data=pendencia
                    )
                    await EmailService.send_email(fiscal_substituto['email'], subject, body, is_html=True)
                    print(f"✅ Email de cancelamento de pendência enviado para o fiscal substituto: {fiscal_substituto['email']}")
        except Exception as e:
            # Log do erro, mas não falha o cancelamento da pendência
            print(f"❌ Erro ao enviar email de cancelamento da pendência {pendencia_id}: {e}")

        # Retorna a pendência atualizada
        return await self.get_pendencia_by_id(pendencia_id)

    async def get_contador_pendencias(self, contrato_id: int, current_user: Usuario) -> dict:
        """Retorna contador de pendências por status para o dashboard"""
        # Verifica se o contrato existe
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")

        # Busca todas as pendências do contrato
        pendencias = await self.pendencia_repo.get_pendencias_by_contrato_id(contrato_id)

        # Conta por status
        contador = {
            "pendentes": 0,                # Pendências aguardando envio de relatório
            "analise_pendente": 0,         # Relatórios aguardando análise do admin
            "concluidas": 0,               # Pendências finalizadas (relatório aprovado)
            "canceladas": 0,               # Pendências canceladas pelo admin
            "total": len(pendencias)
        }

        for pendencia in pendencias:
            status_nome = pendencia.get('status_nome', '').lower()

            if 'pendente' in status_nome:
                contador["pendentes"] += 1
            elif 'concluída' in status_nome:
                contador["concluidas"] += 1
            elif 'cancelada' in status_nome:
                contador["canceladas"] += 1

        # Verifica pendências com relatórios pendentes de análise
        from app.repositories.relatorio_repo import RelatorioRepository
        relatorio_repo = RelatorioRepository(self.pendencia_repo.conn)
        relatorios_pendentes = await relatorio_repo.get_relatorios_pendentes_analise(contrato_id)
        contador["analise_pendente"] = len(relatorios_pendentes)

        # Ajusta contadores - se tem relatório pendente, não deve estar em "pendentes"
        if relatorios_pendentes:
            # Para cada relatório pendente de análise, diminui do contador "pendentes"
            # pois a pendência já tem relatório enviado
            for relatorio in relatorios_pendentes:
                pendencia_id = relatorio.get('pendencia_id')
                # Verifica se esta pendência estava sendo contada como "pendente"
                pendencia_relacionada = next((p for p in pendencias if p['id'] == pendencia_id), None)
                if pendencia_relacionada and 'pendente' in pendencia_relacionada.get('status_nome', '').lower():
                    contador["pendentes"] = max(0, contador["pendentes"] - 1)

        return contador