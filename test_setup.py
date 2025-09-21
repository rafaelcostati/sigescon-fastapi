#!/usr/bin/env python3
"""
Script de teste para validar a estrutura do setup_sistema.sh
"""
import subprocess
import sys

def test_script_structure():
    """Testa se o script tem a estrutura correta"""
    print("🧪 Testando estrutura do script setup_sistema.sh...")

    try:
        # Verifica se o script é executável
        result = subprocess.run(['test', '-x', 'setup_sistema.sh'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Script é executável")
        else:
            print("❌ Script não é executável")
            return False

        # Verifica se contém as funções principais
        with open('setup_sistema.sh', 'r') as f:
            content = f.read()

        required_functions = [
            'setup_basico()',
            'setup_com_dados_teste()',
            'show_menu()',
            'check_prerequisites()'
        ]

        for func in required_functions:
            if func in content:
                print(f"✅ Função {func} encontrada")
            else:
                print(f"❌ Função {func} não encontrada")
                return False

        print("✅ Estrutura do script validada com sucesso!")
        return True

    except Exception as e:
        print(f"❌ Erro ao validar script: {e}")
        return False

def show_script_info():
    """Mostra informações sobre o script"""
    print("\n📋 INFORMAÇÕES DO SCRIPT:")
    print("=" * 50)
    print("📁 Arquivo: setup_sistema.sh")
    print("🎯 Funcionalidade: Script unificado de setup do SIGESCON")
    print("🔄 Substitui: reset_clean.sh, reset_database.sh, reset_examples.sh")
    print("\n📋 Opções disponíveis:")
    print("   1️⃣ Setup Básico - Apenas dados essenciais")
    print("   2️⃣ Setup com Dados de Teste - Dados completos para demonstração")
    print("\n🚀 Para usar:")
    print("   ./setup_sistema.sh")
    print("\n📖 Documentação completa:")
    print("   cat SETUP_SISTEMA_README.md")

if __name__ == "__main__":
    print("🚀 TESTE DO SISTEMA DE SETUP SIGESCON")
    print("=" * 50)

    if test_script_structure():
        show_script_info()
        print("\n✅ Script pronto para uso!")
    else:
        print("\n❌ Script precisa de correções")
        sys.exit(1)