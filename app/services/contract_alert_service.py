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
    async def check_contracts_by_days(target_days: int) -> List[Dict[str, Any]]:
        """
        Busca contratos que vencem exatamente em X dias
        """
        try:
            async for conn in get_connection():
                dashboard_repo = DashboardRepository(conn)
                
                # Buscar todos os contratos próximos ao vencimento
                contratos = await dashboard_repo.get_contratos_proximos_vencimento_admin(target_days + 1)
                
                # Filtrar apenas os que vencem exatamente em target_days
                contratos_filtrados = [
                    contrato for contrato in contratos 
                    if contrato['dias_para_vencer'] == target_days
                ]
                
                return contratos_filtrados
                
        except Exception as e:
            logger.error(f"Erro ao buscar contratos que vencem em {target_days} dias: {e}")
            return []
    
    @staticmethod
    async def send_daily_alerts():
        """
        Método principal para ser chamado diariamente
        Verifica e envia alertas para contratos que vencem em 90, 60 ou 30 dias
        """
        try:
            logger.info("🚀 Iniciando processo diário de alertas de contratos")
            
            admin_emails = await ContractAlertService.get_admin_emails()
            
            if not admin_emails:
                logger.warning("Nenhum administrador encontrado para envio de alertas")
                return
            
            total_alerts = 0
            
            # Verificar cada marco de dias
            for days in [90, 60, 30]:
                contratos = await ContractAlertService.check_contracts_by_days(days)
                
                logger.info(f"Encontrados {len(contratos)} contratos que vencem em {days} dias")
                
                for contrato in contratos:
                    success = await EmailService.send_contract_expiration_alert(
                        admin_emails=admin_emails,
                        contract_data=contrato,
                        days_remaining=days
                    )
                    
                    if success:
                        total_alerts += 1
                        logger.info(f"✅ Alerta enviado: {contrato['contrato_numero']} ({days} dias)")
            
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
