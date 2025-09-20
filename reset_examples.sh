#!/bin/bash
# Script universal para reset com dados de exemplo (funciona local e servidor)

set -e

echo "🔧 SIGESCON - RESET UNIVERSAL (COM DADOS DE EXEMPLO)"
echo "===================================================="

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
echo "   • Modo: DADOS COMPLETOS (básicos + exemplos)"
echo ""

echo "🎭 Dados de exemplo incluem:"
echo "   • 6 usuários com diferentes perfis (alguns com múltiplos perfis)"
echo "   • 5 empresas contratadas"
echo "   • 5 contratos em situações diversas:"
echo "     - Contrato com pendência vencida"
echo "     - Contrato com relatório aguardando análise"
echo "     - Contrato com relatório aprovado"
echo "     - Contrato com pendência ativa"
echo "     - Contrato suspenso"
echo "   • Arquivos PDF de exemplo"
echo "   • Todas as modalidades padrão"
echo ""

# Pergunta confirmação
if [ -t 0 ]; then
    echo "⚠️  ATENÇÃO: Todos os dados serão APAGADOS!"
    echo "Este modo insere dados básicos + dados completos de exemplo para demonstração"
    read -p "Continuar? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "❌ Operação cancelada"
        exit 0
    fi
fi

# Executa reset universal com dados de exemplo
echo "🔄 Executando reset universal com dados de exemplo..."
python scripts/universal_reset.py --examples

echo ""
echo "✅ Reset com dados de exemplo concluído!"
echo "🔗 Acesse: http://localhost:8000/docs"
echo "👤 Login: ${ADMIN_EMAIL:-admin@sigescon.pge.pa.gov.br} / ${ADMIN_PASSWORD:-admin123}"
echo ""
echo "🎯 Usuários de exemplo criados (todos com senha: senha123):"
echo "   • maria.silva@pge.pa.gov.br (Gestor)"
echo "   • joao.oliveira@pge.pa.gov.br (Fiscal)"
echo "   • ana.costa@pge.pa.gov.br (Fiscal)"
echo "   • carlos.lima@pge.pa.gov.br (Gestor + Fiscal)"
echo "   • fernanda.rocha@pge.pa.gov.br (Fiscal)"
echo "   • roberto.almeida@pge.pa.gov.br (Gestor)"