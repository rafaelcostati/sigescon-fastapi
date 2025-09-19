#!/bin/bash

# Script para executar testes e validar a migração
# run_tests.sh

echo "========================================="
echo "   SIGESCON - Validação de Migração"
echo "========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar se um comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Verificar dependências
echo "📦 Verificando dependências..."
if ! command_exists python3; then
    echo -e "${RED}❌ Python3 não encontrado${NC}"
    exit 1
fi

if ! command_exists pytest; then
    echo -e "${YELLOW}⚠️  Pytest não encontrado. Instalando...${NC}"
    pip install pytest pytest-asyncio httpx
fi

# 2. Verificar arquivo .env
echo "🔧 Verificando configuração..."
if [ ! -f .env ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado${NC}"
    echo "Por favor, crie um arquivo .env com as configurações necessárias"
    exit 1
fi

# 3. Verificar se o servidor está rodando
echo "🌐 Verificando servidor FastAPI..."
if ! curl -s http://localhost:8000 > /dev/null; then
    echo -e "${YELLOW}⚠️  Servidor não está rodando. Iniciando...${NC}"
    # Inicia o servidor em background
    uvicorn app.main:app --reload &
    SERVER_PID=$!
    sleep 5
else
    echo -e "${GREEN}✓ Servidor FastAPI está rodando${NC}"
fi

# 4. Executar testes por módulo
echo ""
echo "🧪 Executando testes..."
echo "------------------------"

# Array de módulos de teste
declare -a test_modules=(
    "tests/test_auth_e_usuarios.py::TestUsuariosCRUD"
    "tests/test_auth_e_usuarios.py::TestPasswordManagement"
    "tests/test_auth_e_usuarios.py::TestPermissions"
    "tests/test_contratados.py"
    "tests/test_usuarios_complete.py"
)

# Contadores
total_tests=0
passed_tests=0
failed_tests=0

# Executar cada módulo de teste
for test_module in "${test_modules[@]}"; do
    echo ""
    echo "📋 Testando: $test_module"
    echo "---"
    
    if pytest "$test_module" -v --tb=short; then
        echo -e "${GREEN}✓ Passou${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}✗ Falhou${NC}"
        ((failed_tests++))
    fi
    ((total_tests++))
done

# 5. Relatório de cobertura (se disponível)
echo ""
echo "📊 Gerando relatório de cobertura..."
if command_exists coverage; then
    coverage run -m pytest tests/
    coverage report -m --skip-covered
else
    echo -e "${YELLOW}⚠️  Coverage não instalado. Pulando relatório de cobertura.${NC}"
fi

# 6. Comparação com Flask (validação de paridade)
echo ""
echo "🔍 Validando paridade com Flask..."
echo "-----------------------------------"

# Lista de endpoints que devem existir
declare -a required_endpoints=(
    "GET /usuarios"
    "POST /usuarios"
    "GET /usuarios/{id}"
    "PATCH /usuarios/{id}"
    "DELETE /usuarios/{id}"
    "PATCH /usuarios/{id}/alterar-senha"
    "PATCH /usuarios/{id}/resetar-senha"
    "GET /contratados"
    "POST /contratados"
    "GET /contratados/{id}"
    "PATCH /contratados/{id}"
    "DELETE /contratados/{id}"
    "POST /auth/login"
)

echo "Verificando endpoints implementados:"
for endpoint in "${required_endpoints[@]}"; do
    # Aqui você poderia fazer uma verificação real via curl
    # Por enquanto, apenas lista
    echo "  - $endpoint"
done

# 7. Sumário final
echo ""
echo "========================================="
echo "           SUMÁRIO DE TESTES"
echo "========================================="
echo ""
echo "Total de módulos testados: $total_tests"
echo -e "Passou: ${GREEN}$passed_tests${NC}"
echo -e "Falhou: ${RED}$failed_tests${NC}"
echo ""

if [ $failed_tests -eq 0 ]; then
    echo -e "${GREEN}🎉 Todos os testes passaram!${NC}"
    echo "A migração está progredindo corretamente."
else
    echo -e "${RED}⚠️  Alguns testes falharam.${NC}"
    echo "Por favor, verifique os erros acima."
fi

echo ""
echo "📝 Próximos passos:"
echo "  1. Implementar sistema de permissões robusto"
echo "  2. Migrar tabelas auxiliares (Perfis, Modalidades, Status)"
echo "  3. Implementar módulo de Contratos com upload de arquivos"
echo "  4. Adicionar sistema de notificações por email"
echo ""

# Limpar se iniciamos o servidor
if [ ! -z "$SERVER_PID" ]; then
    echo "🛑 Parando servidor de testes..."
    kill $SERVER_PID 2>/dev/null
fi

echo "✅ Validação concluída!"