#!/bin/bash
# Script para diagnosticar servidor de banco de dados

set -e

echo "🔧 SIGESCON - DIAGNÓSTICO DO SERVIDOR"
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

echo "📋 Conectando em: ${DATABASE_URL}"
echo ""

# Executa diagnóstico
python scripts/diagnose_server.py

echo ""
echo "✅ Diagnóstico concluído!"
echo "Para resetar com segurança, execute: ./safe_reset_server.sh"