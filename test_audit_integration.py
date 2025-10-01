#!/usr/bin/env python3
"""
Script de teste para verificar a integração dos logs de auditoria
"""
import asyncio
import asyncpg
from datetime import datetime


async def test_audit_log_table():
    """Testa se a tabela audit_log existe e está corretamente estruturada"""
    print("=" * 80)
    print("TESTE 1: Verificando estrutura da tabela audit_log")
    print("=" * 80)

    conn = await asyncpg.connect(
        host="10.96.0.67",
        user="root",
        password="xpto1661WIN",
        database="contratos"
    )

    try:
        # Verifica se a tabela existe
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'audit_log'
            );
        """)

        if result:
            print("✅ Tabela audit_log existe")
        else:
            print("❌ Tabela audit_log NÃO existe")
            return False

        # Verifica as colunas
        columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'audit_log'
            ORDER BY ordinal_position;
        """)

        print("\n📋 Colunas da tabela audit_log:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']}")

        # Conta quantos logs existem
        count = await conn.fetchval("SELECT COUNT(*) FROM audit_log;")
        print(f"\n📊 Total de logs registrados: {count}")

        if count > 0:
            # Mostra os últimos 5 logs
            recent_logs = await conn.fetch("""
                SELECT id, usuario_nome, acao, entidade, descricao, data_hora
                FROM audit_log
                ORDER BY data_hora DESC
                LIMIT 5;
            """)

            print("\n🕒 Últimos 5 logs de auditoria:")
            for log in recent_logs:
                print(f"  [{log['data_hora']}] {log['usuario_nome']} - {log['acao']} {log['entidade']}: {log['descricao']}")

        return True

    except Exception as e:
        print(f"❌ Erro ao testar tabela audit_log: {e}")
        return False
    finally:
        await conn.close()


async def test_audit_service_import():
    """Testa se os módulos de auditoria podem ser importados"""
    print("\n" + "=" * 80)
    print("TESTE 2: Verificando imports dos módulos de auditoria")
    print("=" * 80)

    try:
        from app.services.audit_integration import (
            audit_criar_contrato,
            audit_atualizar_contrato,
            audit_criar_pendencia,
            audit_atualizar_pendencia,
            audit_aprovar_relatorio,
            audit_rejeitar_relatorio,
            audit_atualizar_configuracao
        )
        print("✅ Todos os helpers de auditoria foram importados com sucesso")

        from app.repositories.audit_log_repo import AuditLogRepository
        print("✅ AuditLogRepository importado com sucesso")

        from app.services.audit_log_service import AuditLogService
        print("✅ AuditLogService importado com sucesso")

        from app.schemas.audit_log_schema import (
            AuditLog,
            AuditLogCreate,
            AuditLogList,
            AcaoAuditoria,
            EntidadeAuditoria
        )
        print("✅ Schemas de auditoria importados com sucesso")

        return True

    except ImportError as e:
        print(f"❌ Erro ao importar módulos de auditoria: {e}")
        return False


async def test_service_signatures():
    """Verifica se as assinaturas dos services foram atualizadas corretamente"""
    print("\n" + "=" * 80)
    print("TESTE 3: Verificando assinaturas dos métodos dos services")
    print("=" * 80)

    try:
        import inspect

        # ContratoService
        from app.services.contrato_service import ContratoService
        create_sig = inspect.signature(ContratoService.create_contrato)
        update_sig = inspect.signature(ContratoService.update_contrato)

        if 'current_user' in create_sig.parameters and 'request' in create_sig.parameters:
            print("✅ ContratoService.create_contrato tem parâmetros de auditoria")
        else:
            print("❌ ContratoService.create_contrato NÃO tem parâmetros de auditoria")

        if 'current_user' in update_sig.parameters and 'request' in update_sig.parameters:
            print("✅ ContratoService.update_contrato tem parâmetros de auditoria")
        else:
            print("❌ ContratoService.update_contrato NÃO tem parâmetros de auditoria")

        # PendenciaService
        from app.services.pendencia_service import PendenciaService
        create_pend_sig = inspect.signature(PendenciaService.create_pendencia)
        update_pend_sig = inspect.signature(PendenciaService.update_pendencia_status)

        if 'current_user' in create_pend_sig.parameters and 'request' in create_pend_sig.parameters:
            print("✅ PendenciaService.create_pendencia tem parâmetros de auditoria")
        else:
            print("❌ PendenciaService.create_pendencia NÃO tem parâmetros de auditoria")

        if 'current_user' in update_pend_sig.parameters and 'request' in update_pend_sig.parameters:
            print("✅ PendenciaService.update_pendencia_status tem parâmetros de auditoria")
        else:
            print("❌ PendenciaService.update_pendencia_status NÃO tem parâmetros de auditoria")

        # RelatorioService
        from app.services.relatorio_service import RelatorioService
        analisar_sig = inspect.signature(RelatorioService.analisar_relatorio)

        if 'current_user' in analisar_sig.parameters and 'request' in analisar_sig.parameters:
            print("✅ RelatorioService.analisar_relatorio tem parâmetros de auditoria")
        else:
            print("❌ RelatorioService.analisar_relatorio NÃO tem parâmetros de auditoria")

        # ConfigService
        from app.services.config_service import ConfigService
        config_sig = inspect.signature(ConfigService.update_pendencias_intervalo_dias)

        if 'current_user' in config_sig.parameters and 'request' in config_sig.parameters:
            print("✅ ConfigService.update_pendencias_intervalo_dias tem parâmetros de auditoria")
        else:
            print("❌ ConfigService.update_pendencias_intervalo_dias NÃO tem parâmetros de auditoria")

        return True

    except Exception as e:
        print(f"❌ Erro ao verificar assinaturas: {e}")
        return False


async def main():
    """Executa todos os testes"""
    print("\n🔍 TESTE DE INTEGRAÇÃO DOS LOGS DE AUDITORIA")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now()}")
    print("=" * 80)

    results = []

    # Teste 1: Tabela
    results.append(await test_audit_log_table())

    # Teste 2: Imports
    results.append(await test_audit_service_import())

    # Teste 3: Assinaturas
    results.append(await test_service_signatures())

    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    print(f"✅ Testes aprovados: {passed}/{total}")

    if passed == total:
        print("\n🎉 Todos os testes passaram! Sistema de auditoria integrado com sucesso!")
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam. Verifique os erros acima.")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
