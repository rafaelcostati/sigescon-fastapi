#!/usr/bin/env python3
"""
Script de teste para o sistema de alertas de contratos e garantias
"""
import asyncio
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.contract_alert_service import ContractAlertService

async def test_alerts():
    """Executa teste do sistema de alertas"""
    print("=" * 80)
    print("TESTE DO SISTEMA DE ALERTAS DE CONTRATOS E GARANTIAS")
    print("=" * 80)
    print()

    try:
        # Testar busca de emails de administradores
        print("1. Buscando emails de administradores...")
        admin_emails = await ContractAlertService.get_admin_emails()
        print(f"   ✓ Encontrados {len(admin_emails)} emails: {admin_emails}")
        print()

        # Testar busca de contratos por marco
        print("2. Testando busca de contratos por marcos...")
        for milestone in [90, 60, 30]:
            contratos = await ContractAlertService.check_contracts_by_milestone(milestone)
            print(f"   Marco {milestone} dias: {len(contratos)} contratos encontrados")
            if contratos:
                for c in contratos[:3]:  # Mostrar apenas os 3 primeiros
                    print(f"      - {c['contrato_numero']}: {c['dias_para_vencer']} dias")
        print()

        # Testar busca de garantias por marco
        print("3. Testando busca de garantias por marcos...")
        for milestone in [90, 60, 30]:
            garantias = await ContractAlertService.check_garantias_by_milestone(milestone)
            print(f"   Marco {milestone} dias: {len(garantias)} garantias encontradas")
            if garantias:
                for g in garantias[:3]:  # Mostrar apenas as 3 primeiras
                    print(f"      - {g['contrato_numero']}: {g['dias_para_vencer']} dias")
        print()

        # Executar o processo completo de envio de alertas
        print("4. Executando processo completo de envio de alertas...")
        print("   NOTA: Isso enviará emails reais se configurado!")
        response = input("   Deseja continuar? (s/N): ")

        if response.lower() == 's':
            await ContractAlertService.send_daily_alerts()
        else:
            print("   Teste de envio cancelado pelo usuário.")
        print()

        print("=" * 80)
        print("TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERRO durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    print("Iniciando teste do sistema de alertas...")
    print()

    success = asyncio.run(test_alerts())

    sys.exit(0 if success else 1)