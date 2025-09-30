# app/services/notification_service.py
import asyncio
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, date
import logging
from dataclasses import dataclass

from app.services.email_service import EmailService
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.contrato_repo import ContratoRepository

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Tipos de notificação do sistema"""
    PENDENCIA_CRIADA = "pendencia_criada"
    RELATORIO_SUBMETIDO = "relatorio_submetido"
    RELATORIO_APROVADO = "relatorio_aprovado"
    RELATORIO_REJEITADO = "relatorio_rejeitado"
    PRAZO_VENCENDO = "prazo_vencendo"
    PRAZO_VENCIDO = "prazo_vencido"
    CONTRATO_CRIADO = "contrato_criado"
    CONTRATO_VENCENDO = "contrato_vencendo"
    GARANTIA_VENCENDO = "garantia_vencendo"

@dataclass
class NotificationContext:
    """Contexto da notificação com dados necessários"""
    type: NotificationType
    recipient_id: int
    recipient_email: str
    recipient_name: str
    data: Dict  
    priority: str = "normal"  # normal, high, urgent

class NotificationTemplates:
    """Templates de notificação por email"""
    
    @staticmethod
    def get_subject(notification_type: NotificationType, data: Dict) -> str:
        """Retorna o assunto do email baseado no tipo"""
        subjects = {
            NotificationType.PENDENCIA_CRIADA: f"Nova pendência para o contrato {data.get('nr_contrato', 'N/A')}",
            NotificationType.RELATORIO_SUBMETIDO: f"Relatório submetido para análise - {data.get('nr_contrato', 'N/A')}",
            NotificationType.RELATORIO_APROVADO: f"Relatório aprovado - {data.get('nr_contrato', 'N/A')}",
            NotificationType.RELATORIO_REJEITADO: f"Relatório rejeitado - {data.get('nr_contrato', 'N/A')}",
            NotificationType.PRAZO_VENCENDO: f"⚠️ Prazo vencendo em {data.get('dias_restantes', 0)} dias",
            NotificationType.PRAZO_VENCIDO: f"🔴 URGENTE: Prazo vencido - {data.get('nr_contrato', 'N/A')}",
            NotificationType.CONTRATO_CRIADO: f"Novo contrato atribuído: {data.get('nr_contrato', 'N/A')}",
            NotificationType.CONTRATO_VENCENDO: f"⚠️ Contrato vencendo - {data.get('nr_contrato', 'N/A')}",
            NotificationType.GARANTIA_VENCENDO: f"⚠️ Garantia contratual vencendo - {data.get('nr_contrato', 'N/A')}",
        }
        return subjects.get(notification_type, "Notificação do SIGESCON")
    
    @staticmethod
    def get_body(notification_type: NotificationType, context: NotificationContext) -> str:
        """Retorna o corpo do email baseado no tipo"""
        data = context.data
        name = context.recipient_name
        
        if notification_type == NotificationType.PENDENCIA_CRIADA:
            return f"""
Olá, {name},

Uma nova pendência foi criada para você no contrato '{data.get('nr_contrato')}':

📋 Descrição: {data.get('descricao', 'N/A')}
📅 Prazo: {data.get('data_prazo', 'N/A')}
📊 Contrato: {data.get('objeto', 'N/A')}

Por favor, acesse o sistema para submeter o relatório solicitado.

Atenciosamente,
Sistema SIGESCON
            """
        
        elif notification_type == NotificationType.RELATORIO_SUBMETIDO:
            return f"""
Olá, {name},

Um novo relatório foi submetido para análise:

📊 Contrato: {data.get('nr_contrato', 'N/A')} - {data.get('objeto', 'N/A')}
👤 Fiscal: {data.get('fiscal_nome', 'N/A')}
📅 Data de Envio: {data.get('data_envio', 'N/A')}
📝 Observações: {data.get('observacoes_fiscal', 'Sem observações')}

Acesse o sistema para analisar e aprovar/rejeitar o relatório.

Atenciosamente,
Sistema SIGESCON
            """
        
        elif notification_type == NotificationType.RELATORIO_APROVADO:
            return f"""
Olá, {name},

Seu relatório foi aprovado! ✅

📊 Contrato: {data.get('nr_contrato', 'N/A')}
📅 Data de Envio: {data.get('data_envio', 'N/A')}
👤 Aprovado por: {data.get('aprovador_nome', 'N/A')}
📝 Comentários: {data.get('observacoes_aprovador', 'Sem comentários')}

Parabéns pelo trabalho!

Atenciosamente,
Sistema SIGESCON
            """
        
        elif notification_type == NotificationType.RELATORIO_REJEITADO:
            return f"""
Olá, {name},

Seu relatório precisa de correções. 🔄

📊 Contrato: {data.get('nr_contrato', 'N/A')}
📅 Data de Envio: {data.get('data_envio', 'N/A')}
👤 Analisado por: {data.get('aprovador_nome', 'N/A')}

📝 Motivo da rejeição:
{data.get('observacoes_aprovador', 'Não especificado')}

Por favor, faça as correções necessárias e submeta novamente.

Atenciosamente,
Sistema SIGESCON
            """
        
        elif notification_type == NotificationType.PRAZO_VENCENDO:
            dias = data.get('dias_restantes', 0)
            urgencia = "🔴 URGENTE!" if dias <= 1 else "⚠️ Atenção!"

            return f"""
{urgencia}

Olá, {name},

Há uma pendência com prazo próximo do vencimento:

📊 Contrato: {data.get('nr_contrato', 'N/A')}
📋 Descrição: {data.get('descricao', 'N/A')}
📅 Prazo: {data.get('data_prazo', 'N/A')} ({"HOJE" if dias == 0 else f"em {dias} dia(s)"})

{"Submeta o relatório HOJE para evitar atrasos!" if dias <= 1 else "Não se esqueça de submeter o relatório dentro do prazo."}

Atenciosamente,
Sistema SIGESCON
            """

        elif notification_type == NotificationType.GARANTIA_VENCENDO:
            dias = data.get('dias_restantes', 0)
            urgencia = "🔴 CRÍTICO!" if dias <= 30 else "⚠️ Atenção!"

            return f"""
{urgencia}

Prezados Administradores,

A garantia contratual está próxima do vencimento:

📊 Contrato: {data.get('nr_contrato', 'N/A')}
📋 Objeto: {data.get('contrato_objeto', 'N/A')}
🏢 Contratado: {data.get('contratado_nome', 'N/A')}
📅 Vencimento da Garantia: {data.get('data_garantia', 'N/A')} ({dias} dia(s))
👤 Fiscal: {data.get('fiscal_nome', 'N/A')}
👤 Gestor: {data.get('gestor_nome', 'N/A')}

Por favor, providenciar a renovação da garantia com antecedência para evitar problemas contratuais.

Atenciosamente,
Sistema SIGESCON
            """

        return f"Notificação do sistema SIGESCON.\n\nDados: {data}"

class NotificationService:
    """Serviço principal de notificações"""
    
    def __init__(self, usuario_repo: UsuarioRepository, contrato_repo: ContratoRepository):
        self.usuario_repo = usuario_repo
        self.contrato_repo = contrato_repo
        self.templates = NotificationTemplates()
        self.email_queue = asyncio.Queue()  # Fila para processamento assíncrono
    
    async def send_notification(self, context: NotificationContext) -> bool:
        """Envia uma notificação"""
        try:
            subject = self.templates.get_subject(context.type, context.data)
            body = self.templates.get_body(context.type, context)
            
            # Para notificações urgentes, envia imediatamente
            if context.priority == "urgent":
                await EmailService.send_email(context.recipient_email, subject, body, is_html=True)
                logger.info(f"Notificação urgente enviada para {context.recipient_email}")
            else:
                # Adiciona à fila para processamento em lote
                await self.email_queue.put((context.recipient_email, subject, body))
                logger.info(f"Notificação adicionada à fila para {context.recipient_email}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")
            return False
    
    async def notify_pendencia_criada(self, contrato_id: int, pendencia_data: Dict, fiscal_id: int):
        """Notifica fiscal sobre nova pendência"""
        fiscal = await self.usuario_repo.get_user_by_id(fiscal_id)
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        
        if fiscal and contrato:
            context = NotificationContext(
                type=NotificationType.PENDENCIA_CRIADA,
                recipient_id=fiscal['id'],
                recipient_email=fiscal['email'],
                recipient_name=fiscal['nome'],
                data={
                    'nr_contrato': contrato['nr_contrato'],
                    'objeto': contrato['objeto'],
                    'descricao': pendencia_data.get('descricao', ''),
                    'data_prazo': pendencia_data.get('data_prazo', ''),
                },
                priority="high"
            )
            await self.send_notification(context)
    
    async def notify_relatorio_submetido(self, contrato_id: int, relatorio_data: Dict, admin_ids: List[int]):
        """Notifica administradores sobre relatório submetido"""
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        fiscal = await self.usuario_repo.get_user_by_id(relatorio_data['fiscal_usuario_id'])
        
        if contrato and fiscal:
            for admin_id in admin_ids:
                admin = await self.usuario_repo.get_user_by_id(admin_id)
                if admin:
                    context = NotificationContext(
                        type=NotificationType.RELATORIO_SUBMETIDO,
                        recipient_id=admin['id'],
                        recipient_email=admin['email'],
                        recipient_name=admin['nome'],
                        data={
                            'nr_contrato': contrato['nr_contrato'],
                            'objeto': contrato['objeto'],
                            'fiscal_nome': fiscal['nome'],
                            'data_envio': relatorio_data.get('data_envio', ''),
                            'observacoes_fiscal': relatorio_data.get('observacoes_fiscal', ''),
                        }
                    )
                    await self.send_notification(context)
    
    async def process_email_queue(self):
        """Processa fila de emails em lote (para usar em background task)"""
        emails_to_send = []
        
        # Coleta emails da fila (máximo 10 por lote)
        for _ in range(10):
            try:
                email_data = self.email_queue.get_nowait()
                emails_to_send.append(email_data)
            except asyncio.QueueEmpty:
                break
        
        # Envia emails em paralelo
        if emails_to_send:
            tasks = [
                EmailService.send_email(email, subject, body, is_html=True)
                for email, subject, body in emails_to_send
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log dos resultados
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            logger.info(f"Lote de emails processado: {success_count}/{len(emails_to_send)} enviados")
    
    async def check_deadline_reminders(self) -> List[Dict]:
        """Verifica pendências próximas do vencimento"""
        from app.repositories.pendencia_repo import PendenciaRepository
        from app.core.database import get_connection

        # Esta função seria chamada pelo scheduler
        # Retorna lista de pendências que precisam de lembrete
        reminders = []

        try:
            async for conn in get_connection():
                pendencia_repo = PendenciaRepository(conn)
                pendencias_vencendo = await pendencia_repo.get_due_pendencias()
            
            today = date.today()
            
            for pendencia in pendencias_vencendo:
                prazo = pendencia['data_prazo']
                if isinstance(prazo, str):
                    prazo = datetime.strptime(prazo, '%Y-%m-%d').date()
                
                dias_restantes = (prazo - today).days
                
                # Envia lembrete em intervalos específicos
                if dias_restantes in [15, 7, 3, 1, 0, -1]:  # Incluindo 1 dia de atraso
                    priority = "urgent" if dias_restantes <= 0 else "high" if dias_restantes <= 1 else "normal"
                    notification_type = NotificationType.PRAZO_VENCIDO if dias_restantes < 0 else NotificationType.PRAZO_VENCENDO
                    
                    context = NotificationContext(
                        type=notification_type,
                        recipient_id=0,  # Será preenchido quando buscar o fiscal
                        recipient_email=pendencia['fiscal_email'],
                        recipient_name=pendencia['fiscal_nome'],
                        data={
                            'nr_contrato': pendencia['nr_contrato'],
                            'descricao': pendencia['descricao'],
                            'data_prazo': prazo.strftime('%d/%m/%Y'),
                            'dias_restantes': dias_restantes,
                        },
                        priority=priority
                    )
                    
                    await self.send_notification(context)
                    reminders.append(pendencia)

                return reminders
        
        except Exception as e:
            logger.error(f"Erro ao verificar lembretes de prazo: {e}")
            return []

# app/tasks/notification_tasks.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.notification_service import NotificationService
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.contrato_repo import ContratoRepository
from app.core.database import get_db_pool
import logging

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Agendador de tarefas de notificação"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
        self.notification_service = None
    
    async def setup_services(self):
        """Inicializa os serviços necessários"""
        # Os repositórios serão criados nas funções individuais com conexões próprias
        # para evitar problemas de pool
        pass
    
    async def process_notification_queue(self):
        """Task para processar fila de notificações"""
        try:
            if self.notification_service:
                await self.notification_service.process_email_queue()
        except Exception as e:
            logger.error(f"Erro ao processar fila de notificações: {e}")
    
    async def check_deadlines(self):
        """Task para verificar prazos vencendo"""
        from app.core.database import get_connection
        from app.repositories.usuario_repo import UsuarioRepository
        from app.repositories.contrato_repo import ContratoRepository

        try:
            async for conn in get_connection():
                usuario_repo = UsuarioRepository(conn)
                contrato_repo = ContratoRepository(conn)
                notification_service = NotificationService(usuario_repo, contrato_repo)

                reminders_sent = await notification_service.check_deadline_reminders()
                logger.info(f"Verificação de prazos concluída. {len(reminders_sent)} lembretes enviados.")
        except Exception as e:
            logger.error(f"Erro ao verificar lembretes de prazo: {e}")
    
    async def check_contract_expiration_alerts(self):
        """Task para verificar contratos e garantias próximos ao vencimento (executada a cada 5 dias às 10h)"""
        try:
            from app.services.contract_alert_service import ContractAlertService
            await ContractAlertService.send_daily_alerts()
            logger.info("Verificação de contratos e garantias próximos ao vencimento concluída.")
        except Exception as e:
            logger.error(f"Erro ao verificar contratos e garantias próximos ao vencimento: {e}")
    
    def start_scheduler(self):
        """Inicia o agendador de tarefas"""
        # Processa fila de emails a cada 5 minutos
        self.scheduler.add_job(
            self.process_notification_queue,
            'interval',
            minutes=5,
            id='process_notifications',
            max_instances=1
        )
        
        # Verifica prazos todos os dias às 8h e às 17h
        self.scheduler.add_job(
            self.check_deadlines,
            'cron',
            hour='8,17',
            minute=0,
            id='check_deadlines',
            max_instances=1
        )
        
        # Verifica contratos e garantias próximos ao vencimento a cada 5 dias às 10h
        self.scheduler.add_job(
            self.check_contract_expiration_alerts,
            'cron',
            day='*/5',
            hour=10,
            minute=0,
            id='check_contract_expiration',
            max_instances=1
        )
        
        self.scheduler.start()
        logger.info("Scheduler de notificações iniciado (alertas de contratos/garantias a cada 5 dias às 10h)")
    
    def stop_scheduler(self):
        """Para o agendador"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler de notificações parado")
