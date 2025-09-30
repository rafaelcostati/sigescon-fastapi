#!/usr/bin/env python3
"""
Script de teste silencioso para o sistema de alertas (sem enviar emails)
"""
import asyncio
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.contract_alert_service import ContractAlertService

async def test_alerts_silent():
    """Executa teste do sistema de alertas SEM ENVIAR EMAILS"""
    print("=" * 80)
    print("TESTE DO SISTEMA DE ALERTAS DE CONTRATOS E GARANTIAS (MODO SILENCIOSO)")
    print("=" * 80)
    print()

    try:
        # Testar busca de emails de administradores
        print("1. Buscando emails de administradores...")
        admin_emails = await ContractAlertService.get_admin_emails()
        print(f"   ✓ Encontrados {len(admin_emails)} emails")
        print()

        # Resumo geral
        total_contratos = 0
        total_garantias = 0

        # Testar busca de contratos por marco
        print("2. Contratos próximos ao vencimento:")
        for milestone in [90, 60, 30]:
            contratos = await ContractAlertService.check_contracts_by_milestone(milestone)
            total_contratos += len(contratos)
            print(f"   Marco {milestone} dias: {len(contratos)} contratos")
            if contratos:
                for c in contratos:
                    print(f"      - {c['contrato_numero']}: {c['dias_para_vencer']} dias (ID: {c['contrato_id']})")
        print()

        # Testar busca de garantias por marco
        print("3. Garantias próximas ao vencimento:")
        for milestone in [90, 60, 30]:
            garantias = await ContractAlertService.check_garantias_by_milestone(milestone)
            total_garantias += len(garantias)
            print(f"   Marco {milestone} dias: {len(garantias)} garantias")
            if garantias:
                for g in garantias:
                    print(f"      - {g['contrato_numero']}: {g['dias_para_vencer']} dias (ID: {g['contrato_id']})")
        print()

        print("=" * 80)
        print("RESUMO:")
        print(f"  - Total de alertas de contratos a enviar: {total_contratos}")
        print(f"  - Total de alertas de garantias a enviar: {total_garantias}")
        print(f"  - Total de alertas: {total_contratos + total_garantias}")
        print(f"  - Destinatários: {len(admin_emails)} administradores")
        print("=" * 80)
        print("✓ TESTE CONCLUÍDO COM SUCESSO!")
        print()
        print("NOTA: Para enviar os alertas realmente, execute o scheduler ou rode manualmente")
        print("      o método ContractAlertService.send_daily_alerts()")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERRO durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_alerts_silent())
    sys.exit(0 if success else 1)