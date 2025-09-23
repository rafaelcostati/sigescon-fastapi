#!/usr/bin/env python3
"""
Teste para verificar se a criação de contrato está funcionando após correções
"""
import asyncio
from datetime import date

async def test_contrato_creation():
    """Teste de criação de contrato"""
    try:
        print("🧪 Testando criação de contrato após correções...")

        # Importar schemas necessários
        from app.schemas.contrato_schema import ContratoCreate

        # Criar dados de teste
        contrato_data = ContratoCreate(
            nr_contrato="TESTE_123",
            objeto="Teste de contrato para validação",
            data_inicio=date.today(),
            data_fim=date(2025, 12, 31),
            contratado_id=1,
            modalidade_id=1,
            status_id=1,
            gestor_id=1,
            fiscal_id=2,
            valor_anual=50000.00,
            valor_global=100000.00,
            base_legal="Lei 8.666/93",
            termos_contratuais="Termos de teste",
            pae="PAE123",
            doe="DOE456",
            data_doe=date.today()
        )

        print("✅ ContratoCreate criado com sucesso")
        print(f"   Dados: {contrato_data.model_dump()}")

        # Testar se o model_dump não gera problemas
        data_dict = contrato_data.model_dump()
        print(f"✅ model_dump() executado: {len(data_dict)} campos")

        # Verificar tipos dos campos
        for field, value in data_dict.items():
            print(f"   {field}: {type(value).__name__} = {value}")

        return True

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_imports():
    """Teste de importações necessárias"""
    try:
        print("\n🔍 Testando importações...")

        from app.repositories.contrato_repo import ContratoRepository
        print("✅ ContratoRepository importado")

        from app.services.contrato_service import ContratoService
        print("✅ ContratoService importado")

        from app.main import app
        print("✅ FastAPI app importada")

        return True

    except Exception as e:
        print(f"❌ Erro nas importações: {e}")
        return False

async def main():
    """Função principal"""
    print("🚀 TESTE DE CORREÇÕES - CRIAÇÃO DE CONTRATO")
    print("=" * 50)

    # Teste 1: Importações
    success1 = await test_imports()

    # Teste 2: Criação de contrato
    success2 = await test_contrato_creation()

    # Resultado
    print("\n" + "=" * 50)
    print("📊 RESULTADO")
    print("=" * 50)

    if success1 and success2:
        print("✅ TESTES PASSARAM!")
        print("🎉 Correções aplicadas com sucesso!")
        print("📤 Sistema pronto para teste de upload no frontend")
        exit_code = 0
    else:
        print("❌ TESTES FALHARAM!")
        print("🔧 Verifique os logs acima")
        exit_code = 1

    return exit_code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)