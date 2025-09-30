# app/services/contract_alert_service.py
import asyncio
import logging
from datetime import date, timedelta
from typing import List, Dict, Any
from app.core.database import get_connection
from app.repositories.dashboard_repo import DashboardRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

class ContractAlertService:
    """
    Serviço responsável por verificar contratos próximos ao vencimento
    e enviar alertas por email para administradores
    """
    
    @staticmethod
    async def get_admin_emails() -> List[str]:
        """
        Busca emails de todos os usuários com perfil de Administrador
        """
        try:
            async for conn in get_connection():
                # Query para buscar emails de administradores
                query = """
                SELECT DISTINCT u.email
                FROM usuario u
                JOIN usuario_perfil up ON u.id = up.usuario_id
                JOIN perfil p ON up.perfil_id = p.id
                WHERE p.nome = 'Administrador'
                AND u.ativo = true
                AND u.email IS NOT NULL
                """

                rows = await conn.fetch(query)
                emails = [row['email'] for row in rows if row['email']]

                logger.info(f"Encontrados {len(emails)} emails de administradores")
                return emails

        except Exception as e:
            logger.error(f"Erro ao buscar emails de administradores: {e}")
            return []
    
    @staticmethod
    async def check_and_send_alerts():
        """
        Verifica contratos próximos ao vencimento e envia alertas
        """
        try:
            logger.info("🔍 Iniciando verificação de contratos próximos ao vencimento...")
            
            async for conn in get_connection():
                dashboard_repo = DashboardRepository(conn)
                
                # Buscar contratos que vencem em 90, 60 ou 30 dias
                contratos_90_dias = await dashboard_repo.get_contratos_proximos_vencimento_admin(90)
                
                if not contratos_90_dias:
                    logger.info("Nenhum contrato próximo ao vencimento encontrado")
                    return
                
                # Buscar emails dos administradores
                admin_emails = await ContractAlertService.get_admin_emails()
                
                if not admin_emails:
                    logger.warning("Nenhum email de administrador encontrado")
                    return
                
                alerts_sent = 0
                today = date.today()
                
                for contrato in contratos_90_dias:
                    dias_para_vencer = contrato['dias_para_vencer']
                    
                    # Enviar alertas apenas em marcos específicos: 90, 60, 30 dias
                    if dias_para_vencer in [90, 60, 30]:
                        logger.info(f"📧 Enviando alerta para contrato {contrato['contrato_numero']} ({dias_para_vencer} dias)")
                        
                        success = await EmailService.send_contract_expiration_alert(
                            admin_emails=admin_emails,
                            contract_data=contrato,
                            days_remaining=dias_para_vencer
                        )
                        
                        if success:
                            alerts_sent += 1
                            logger.info(f"✅ Alerta enviado para contrato {contrato['contrato_numero']}")
                        else:
                            logger.error(f"❌ Falha ao enviar alerta para contrato {contrato['contrato_numero']}")
                
                logger.info(f"🎯 Processo concluído: {alerts_sent} alertas enviados")
                
        except Exception as e:
            logger.error(f"❌ Erro no processo de alertas de contratos: {e}")
    
    @staticmethod
    async def check_contracts_by_milestone(milestone_days: int) -> List[Dict[str, Any]]:
        """
        Busca contratos que estão na faixa do marco (<=90, <=60, <=30 dias)
        e ainda não foram notificados para este marco específico
        """
        try:
            async for conn in get_connection():
                dashboard_repo = DashboardRepository(conn)

                # Buscar contratos próximos ao vencimento dentro da faixa do marco
                contratos = await dashboard_repo.get_contratos_proximos_vencimento_admin(milestone_days)

                # Filtrar apenas contratos dentro da faixa do marco atual
                # Ex: para marco 60, pega contratos com <= 60 dias E que não foram notificados ainda
                if milestone_days == 90:
                    # Marco 90: contratos entre 61 e 90 dias
                    contratos_filtrados = [c for c in contratos if 61 <= c['dias_para_vencer'] <= 90]
                elif milestone_days == 60:
                    # Marco 60: contratos entre 31 e 60 dias
                    contratos_filtrados = [c for c in contratos if 31 <= c['dias_para_vencer'] <= 60]
                elif milestone_days == 30:
                    # Marco 30: contratos com <= 30 dias
                    contratos_filtrados = [c for c in contratos if c['dias_para_vencer'] <= 30]
                else:
                    contratos_filtrados = contratos

                # Verificar quais já foram notificados para este marco
                contratos_pendentes = []
                for contrato in contratos_filtrados:
                    # Verificar se já existe notificação para este contrato neste marco
                    check_query = """
                        SELECT 1 FROM notification_log
                        WHERE notification_type = 'contract_expiration'
                        AND contrato_id = $1
                        AND alert_milestone = $2
                    """
                    exists = await conn.fetchval(check_query, contrato['contrato_id'], milestone_days)

                    if not exists:
                        contratos_pendentes.append(contrato)

                logger.info(f"Encontrados {len(contratos_pendentes)} contratos para notificar no marco de {milestone_days} dias")
                return contratos_pendentes

        except Exception as e:
            logger.error(f"Erro ao buscar contratos no marco de {milestone_days} dias: {e}")
            return []
    
    @staticmethod
    async def check_garantias_by_milestone(milestone_days: int) -> List[Dict[str, Any]]:
        """
        Busca contratos com garantias que estão na faixa do marco (<=90, <=60, <=30 dias)
        e ainda não foram notificados para este marco específico
        """
        try:
            async for conn in get_connection():
                dashboard_repo = DashboardRepository(conn)

                # Buscar garantias próximas ao vencimento dentro da faixa do marco
                garantias = await dashboard_repo.get_garantias_proximas_vencimento_admin(milestone_days)

                # Filtrar apenas garantias dentro da faixa do marco atual
                if milestone_days == 90:
                    # Marco 90: garantias entre 61 e 90 dias
                    garantias_filtradas = [g for g in garantias if 61 <= g['dias_para_vencer'] <= 90]
                elif milestone_days == 60:
                    # Marco 60: garantias entre 31 e 60 dias
                    garantias_filtradas = [g for g in garantias if 31 <= g['dias_para_vencer'] <= 60]
                elif milestone_days == 30:
                    # Marco 30: garantias com <= 30 dias
                    garantias_filtradas = [g for g in garantias if g['dias_para_vencer'] <= 30]
                else:
                    garantias_filtradas = garantias

                # Verificar quais já foram notificados para este marco
                garantias_pendentes = []
                for garantia in garantias_filtradas:
                    # Verificar se já existe notificação para esta garantia neste marco
                    check_query = """
                        SELECT 1 FROM notification_log
                        WHERE notification_type = 'garantia_expiration'
                        AND contrato_id = $1
                        AND alert_milestone = $2
                    """
                    exists = await conn.fetchval(check_query, garantia['contrato_id'], milestone_days)

                    if not exists:
                        garantias_pendentes.append(garantia)

                logger.info(f"Encontrados {len(garantias_pendentes)} garantias para notificar no marco de {milestone_days} dias")
                return garantias_pendentes

        except Exception as e:
            logger.error(f"Erro ao buscar garantias no marco de {milestone_days} dias: {e}")
            return []

    @staticmethod
    async def send_daily_alerts():
        """
        Método principal para ser chamado diariamente
        Verifica e envia alertas para contratos e garantias que vencem em 90, 60 ou 30 dias
        """
        try:
            logger.info("🚀 Iniciando processo diário de alertas de contratos e garantias")

            admin_emails = await ContractAlertService.get_admin_emails()

            if not admin_emails:
                logger.warning("Nenhum administrador encontrado para envio de alertas")
                return

            total_alerts = 0

            async for conn in get_connection():
                # Verificar cada marco de dias para CONTRATOS
                for milestone in [90, 60, 30]:
                    contratos = await ContractAlertService.check_contracts_by_milestone(milestone)

                    logger.info(f"Encontrados {len(contratos)} contratos que vencem em {milestone} dias")

                    for contrato in contratos:
                        success = await EmailService.send_contract_expiration_alert(
                            admin_emails=admin_emails,
                            contract_data=contrato,
                            days_remaining=milestone
                        )

                        if success:
                            # Registrar notificação enviada
                            insert_query = """
                                INSERT INTO notification_log (notification_type, contrato_id, alert_milestone)
                                VALUES ('contract_expiration', $1, $2)
                                ON CONFLICT (notification_type, contrato_id, alert_milestone) DO NOTHING
                            """
                            await conn.execute(insert_query, contrato['contrato_id'], milestone)

                            total_alerts += 1
                            logger.info(f"✅ Alerta de contrato enviado: {contrato['contrato_numero']} ({milestone} dias)")

                # Verificar cada marco de dias para GARANTIAS
                for milestone in [90, 60, 30]:
                    garantias = await ContractAlertService.check_garantias_by_milestone(milestone)

                    logger.info(f"Encontrados {len(garantias)} garantias que vencem em {milestone} dias")

                    for garantia in garantias:
                        success = await EmailService.send_garantia_expiration_alert(
                            admin_emails=admin_emails,
                            garantia_data=garantia,
                            days_remaining=milestone
                        )

                        if success:
                            # Registrar notificação enviada
                            insert_query = """
                                INSERT INTO notification_log (notification_type, contrato_id, alert_milestone)
                                VALUES ('garantia_expiration', $1, $2)
                                ON CONFLICT (notification_type, contrato_id, alert_milestone) DO NOTHING
                            """
                            await conn.execute(insert_query, garantia['contrato_id'], milestone)

                            total_alerts += 1
                            logger.info(f"✅ Alerta de garantia enviado: {garantia['contrato_numero']} ({milestone} dias)")

            logger.info(f"🎯 Processo diário concluído: {total_alerts} alertas enviados")

        except Exception as e:
            logger.error(f"❌ Erro no processo diário de alertas: {e}")

# Função para ser chamada por um scheduler (cron, celery, etc.)
async def run_daily_contract_alerts():
    """
    Função wrapper para execução em scheduler
    """
    await ContractAlertService.send_daily_alerts()

if __name__ == "__main__":
    # Para teste manual
    asyncio.run(ContractAlertService.send_daily_alerts())
