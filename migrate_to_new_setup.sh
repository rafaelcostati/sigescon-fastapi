#!/bin/bash
# migrate_to_new_setup.sh
# Script para migrar dos scripts antigos para o novo setup_sistema.sh

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              MIGRAÇÃO PARA NOVO SISTEMA DE SETUP            ║"
echo "║                        SIGESCON v2.0                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}📋 O que este script faz:${NC}"
echo "   • Remove scripts antigos (reset_*.sh)"
echo "   • Mostra como usar o novo setup_sistema.sh"
echo "   • Preserva configurações importantes"
echo ""

# Verificar se os scripts antigos existem
old_scripts=("reset_clean.sh" "reset_database.sh" "reset_examples.sh")
scripts_found=()

for script in "${old_scripts[@]}"; do
    if [ -f "$script" ]; then
        scripts_found+=("$script")
    fi
done

if [ ${#scripts_found[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ Nenhum script antigo encontrado. Migração não necessária.${NC}"
else
    echo -e "${YELLOW}📁 Scripts antigos encontrados:${NC}"
    for script in "${scripts_found[@]}"; do
        echo "   • $script"
    done
    echo ""

    read -p "$(echo -e ${YELLOW}Remover scripts antigos? \(s/N\): ${NC})" -n 1 -r
    echo

    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}🗑️  Removendo scripts antigos...${NC}"
        for script in "${scripts_found[@]}"; do
            rm -f "$script"
            echo -e "${GREEN}   ✓ $script removido${NC}"
        done
        echo -e "${GREEN}✅ Scripts antigos removidos com sucesso!${NC}"
    else
        echo -e "${YELLOW}📝 Scripts antigos mantidos (recomenda-se remoção manual depois)${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🚀 NOVO SISTEMA DE SETUP DISPONÍVEL!${NC}"
echo "="*50

echo -e "${BLUE}📋 Como usar o novo sistema:${NC}"
echo ""
echo -e "${GREEN}1. Para ambiente de produção (apenas essencial):${NC}"
echo "   ./setup_sistema.sh"
echo "   # Escolher opção 1"
echo ""
echo -e "${GREEN}2. Para desenvolvimento/testes (com exemplos):${NC}"
echo "   ./setup_sistema.sh"
echo "   # Escolher opção 2"
echo ""

echo -e "${YELLOW}📊 Diferenças do novo sistema:${NC}"
echo "✅ Interface amigável com menu interativo"
echo "✅ Validações automáticas de pré-requisitos"
echo "✅ Dados de teste mais completos e realistas"
echo "✅ Status 'Aguardando Análise' incluído"
echo "✅ Usuários com múltiplos perfis configurados"
echo "✅ Pendências em todos os status para testes"
echo "✅ Contratos completos com arquivos de exemplo"
echo ""

echo -e "${BLUE}📖 Documentação completa:${NC}"
echo "   cat SETUP_SISTEMA_README.md"
echo ""

echo -e "${GREEN}🎯 Pronto para usar! Execute:${NC}"
echo -e "${YELLOW}   ./setup_sistema.sh${NC}"

# Verificar se setup_sistema.sh existe e é executável
if [ ! -f "setup_sistema.sh" ]; then
    echo -e "${RED}❌ Erro: setup_sistema.sh não encontrado!${NC}"
    exit 1
fi

if [ ! -x "setup_sistema.sh" ]; then
    echo -e "${YELLOW}🔧 Tornando setup_sistema.sh executável...${NC}"
    chmod +x setup_sistema.sh
    echo -e "${GREEN}✅ Pronto!${NC}"
fi

echo ""
echo -e "${GREEN}✅ Migração concluída com sucesso!${NC}"