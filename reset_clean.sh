#!/bin/bash
# Script para resetar banco de dados SIGESCON - MODO CLEAN
# Cria apenas dados essenciais (perfis, status, admin)

set -e  # Sair se houver erro

echo "🚀 SIGESCON - Reset CLEAN do Banco de Dados"
echo "==========================================="
echo "Este script criará apenas dados essenciais:"
echo "   • Perfis (Administrador, Gestor, Fiscal)"
echo "   • Modalidades de contrato"
echo "   • Status (contrato, relatório, pendência)"
echo "   • Usuário administrador do .env"
echo ""

# Verifica se está no diretório correto
if [ ! -f "app/main.py" ]; then
    echo "❌ Execute este script a partir do diretório raiz do projeto backend"
    exit 1
fi

# Verifica se o ambiente virtual está ativo
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Ambiente virtual não detectado. Ativando..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "✅ Ambiente virtual ativado"
    else
        echo "❌ Ambiente virtual .venv não encontrado"
        echo "Execute: python -m venv .venv && source .venv/bin/activate && pip install -e ."
        exit 1
    fi
fi

# Verifica se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado"
    echo "Crie um arquivo .env com as configurações do banco"
    exit 1
fi

# Carrega variáveis do .env
export $(grep -v '^#' .env | xargs)

echo "📋 Configurações:"
echo "   • Banco: ${DATABASE_URL:-Local}"
echo "   • Admin: ${ADMIN_EMAIL:-admin@sigescon.gov.br}"
echo ""

# Pergunta confirmação (apenas se executado interativamente)
if [ -t 0 ]; then
    echo "⚠️  ATENÇÃO: Todos os dados serão APAGADOS!"
    read -p "Continuar? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "❌ Operação cancelada"
        exit 0
    fi
fi

# Executa o script Python em modo clean
echo "🔄 Executando reset clean..."
python scripts/quick_reset.py --clean

echo ""
echo "✅ Banco resetado com sucesso (modo clean)!"
echo "🔗 Acesse: http://localhost:8000/docs"
echo "👤 Login: ${ADMIN_EMAIL:-admin@sigescon.gov.br} / ${ADMIN_PASSWORD:-admin123}"
echo ""
echo "💡 Para criar dados de exemplo, use: ./reset_database.sh"