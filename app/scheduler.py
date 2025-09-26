# app/scheduler.py
import asyncio
from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import get_db_pool, close_db_pool
from app.repositories.pendencia_repo import PendenciaRepository
from app.services.email_service import EmailService

async def check_deadlines_async():
    """
    Função assíncrona que o scheduler irá executar para verificar os prazos.
    """
    print("Executando verificação de prazos de pendências...")
    pool = None
    conn = None
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            pendencia_repo = PendenciaRepository(conn)
            pendencias = await pendencia_repo.get_due_pendencias()
            
            today = date.today()
            
            for p in pendencias:
                prazo = p['data_prazo']
                dias_restantes = (prazo - today).days
                
                # Envia lembrete 15, 5, 3 dias antes, ou no dia do vencimento
                dias_lembrete = [15, 5, 3, 0]
                
                if dias_restantes in dias_lembrete:
                    subject = f"Lembrete de Prazo: Pendência do Contrato {p['nr_contrato']}"
                    
                    if dias_restantes > 0:
                        prazo_str = f"expira em {dias_restantes} dia(s) ({prazo.strftime('%d/%m/%Y')})."
                    elif dias_restantes == 0:
                        prazo_str = f"expira HOJE ({prazo.strftime('%d/%m/%Y')})."
                    else:
                        continue # Não envia e-mail para prazos já vencidos

                    body = f"""
Olá, {p['fiscal_nome']},

Este é um lembrete automático sobre uma pendência de relatório para o contrato '{p['nr_contrato']}'.

- Descrição: {p['descricao']}
- O prazo para envio {prazo_str}

Por favor, não se esqueça de submeter o relatório a tempo.
                    """
                    await EmailService.send_email(p['fiscal_email'], subject, body, is_html=True)
                    
    except Exception as e:
        print(f"ERRO ao executar a verificação de prazos: {e}")
    finally:
        if pool:
            await close_db_pool()
        print("Verificação de prazos concluída.")


async def main():
    """Função principal para iniciar o scheduler."""
    scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
    
    # Agenda a tarefa para rodar todos os dias às 8h da manhã
    scheduler.add_job(check_deadlines_async, 'cron', hour=8, minute=0)
    
    # Para testes, pode descomentar a linha abaixo para rodar a cada minuto
    # scheduler.add_job(check_deadlines_async, 'interval', minutes=1)
    
    scheduler.start()
    print("Agendador de lembretes iniciado. Pressione Ctrl+C para sair.")
    
    # Mantém o script a correr
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        await close_db_pool()


if __name__ == "__main__":
    asyncio.run(main())