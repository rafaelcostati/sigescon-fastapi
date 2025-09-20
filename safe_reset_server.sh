#!/bin/bash
# Script para reset seguro do servidor (sem privilégios de superusuário)

set -e

echo "🔧 SIGESCON - RESET SEGURO DO SERVIDOR"
echo "===================================="

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
        exit 1
    fi
fi

# Verifica se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado"
    exit 1
fi

# Carrega variáveis do .env
export $(grep -v '^#' .env | xargs)

echo "📋 Configurações:"
echo "   • Banco: ${DATABASE_URL}"
echo "   • Admin: ${ADMIN_EMAIL:-admin@sigescon.pge.pa.gov.br}"
echo ""

# Pergunta confirmação
if [ -t 0 ]; then
    echo "⚠️  ATENÇÃO: Todos os dados serão APAGADOS!"
    echo "Este script usa método seguro (sem privilégios de superusuário)"
    read -p "Continuar? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "❌ Operação cancelada"
        exit 0
    fi
fi

# Executa reset seguro
echo "🔄 Executando reset seguro..."
python scripts/safe_reset_server.py

echo ""
echo "✅ Reset concluído!"
echo "🔗 Acesse: http://10.96.0.67:8000/docs"
echo "👤 Login: ${ADMIN_EMAIL:-admin@sigescon.pge.pa.gov.br} / ${ADMIN_PASSWORD:-admin123}"