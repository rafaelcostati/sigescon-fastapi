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
    Usa configurações dinâmicas do banco de dados.
    """
    print("Executando verificação de prazos de pendências...")
    pool = None
    conn = None
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            from app.repositories.config_repo import ConfigRepository
            
            pendencia_repo = PendenciaRepository(conn)
            config_repo = ConfigRepository(conn)
            
            # Busca configurações dinâmicas
            dias_antes_inicio = await config_repo.get_lembretes_dias_antes_inicio()
            intervalo_dias = await config_repo.get_lembretes_intervalo_dias()
            
            print(f"📋 Configurações de lembretes: Início={dias_antes_inicio} dias antes, Intervalo={intervalo_dias} dias")
            
            # Calcula os dias de lembrete baseado nas configurações
            dias_lembrete = []
            dia_atual = dias_antes_inicio
            while dia_atual >= 0:
                dias_lembrete.append(dia_atual)
                dia_atual -= intervalo_dias
            
            # Garante que o dia 0 (vencimento) esteja incluído
            if 0 not in dias_lembrete:
                dias_lembrete.append(0)
            
            dias_lembrete = sorted(set(dias_lembrete), reverse=True)  # Remove duplicatas e ordena
            print(f"📅 Lembretes serão enviados nos seguintes dias antes do vencimento: {dias_lembrete}")
            
            pendencias = await pendencia_repo.get_due_pendencias()
            today = date.today()
            
            emails_enviados = 0
            for p in pendencias:
                prazo = p['data_prazo']
                dias_restantes = (prazo - today).days
                
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
                    emails_enviados += 1
                    print(f"✅ Email enviado para {p['fiscal_nome']} - Pendência vence em {dias_restantes} dia(s)")
            
            print(f"📧 Total de emails de lembrete enviados: {emails_enviados}")
                    
    except Exception as e:
        print(f"ERRO ao executar a verificação de prazos: {e}")
        import traceback
        print(traceback.format_exc())
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