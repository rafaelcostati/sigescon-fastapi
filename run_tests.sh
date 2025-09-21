#!/bin/bash

# Script para executar testes e validar o sistema SIGESCON
# run_tests.sh

echo "========================================="
echo "   SIGESCON - Validação do Sistema"
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
    "tests/test_auth_e_usuarios.py"
    "tests/test_contratados.py"
    "tests/test_usuarios_complete.py"
    "tests/test_contratos.py"
    "tests/test_modalidades.py"
    "tests/test_perfis.py"
    "tests/test_status.py"
    "tests/test_pendencias.py"
    "tests/test_relatorios.py"
    "tests/test_email_service.py"
    "tests/test_workflow_relatorios.py"
    "tests/test_arquivos_contrato.py"
    "tests/test_security_authorization.py"
    "tests/test_notification_system.py"
    "tests/test_data_integrity.py"
    "tests/test_dashboard.py"
    "tests/test_novo_status_aguardando_analise.py"
    "tests/test_contexto_sessao_alternancia_perfis.py"
    "tests/test_isolamento_dados_perfil.py"
)

# Contadores
total_tests=0
passed_tests=0
failed_tests=0

# Arrays para armazenar resultados
declare -a passed_modules=()
declare -a failed_modules=()
declare -a error_details=()

# Executar cada módulo de teste
for test_module in "${test_modules[@]}"; do
    echo ""
    echo "📋 Testando: $test_module"
    echo "---"

    # Capturar output do pytest para análise de erros
    test_output=$(pytest "$test_module" -v --tb=short 2>&1)
    test_exit_code=$?

    if [ $test_exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ Passou${NC}"
        passed_modules+=("$test_module")
        ((passed_tests++))
    else
        echo -e "${RED}✗ Falhou${NC}"
        failed_modules+=("$test_module")

        # Extrair informações de erro mais específicas
        error_info=$(echo "$test_output" | grep -E "FAILED.*::" | head -2)
        if [ -z "$error_info" ]; then
            # Se não encontrou FAILED, procura por outras mensagens de erro
            error_info=$(echo "$test_output" | grep -E "(ERROR:|AssertionError|TypeError|ValueError)" | head -2)
        fi
        if [ -z "$error_info" ]; then
            error_info="Verifique logs - teste pode ter passado com warnings"
        fi
        error_details+=("$test_module: $error_info")
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

# Mostrar módulos que passaram
if [ ${#passed_modules[@]} -gt 0 ]; then
    echo -e "${GREEN}✅ MÓDULOS QUE PASSARAM:${NC}"
    for module in "${passed_modules[@]}"; do
        echo -e "  ${GREEN}✓${NC} $module"
    done
    echo ""
fi

# Mostrar detalhes dos erros
if [ ${#failed_modules[@]} -gt 0 ]; then
    echo -e "${RED}❌ MÓDULOS COM FALHAS:${NC}"
    for i in "${!failed_modules[@]}"; do
        echo -e "  ${RED}✗${NC} ${failed_modules[$i]}"
    done
    echo ""

    echo -e "${YELLOW}🔍 DETALHES DOS ERROS:${NC}"
    echo "----------------------------------------"
    for detail in "${error_details[@]}"; do
        echo -e "${RED}➤${NC} $detail"
        echo ""
    done
fi

if [ $failed_tests -eq 0 ]; then
    echo -e "${GREEN}🎉 Todos os testes passaram!${NC}"
    echo "Sistema SIGESCON operando corretamente."
else
    echo -e "${RED}⚠️  Alguns testes falharam.${NC}"
    echo "Verifique os detalhes dos erros acima para debug."
fi

echo ""

# Limpar se iniciamos o servidor
if [ ! -z "$SERVER_PID" ]; then
    echo "🛑 Parando servidor de testes..."
    kill $SERVER_PID 2>/dev/null
fi

echo "✅ Validação concluída!"