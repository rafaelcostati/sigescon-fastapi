#!/bin/bash
# setup_sistema.sh - Script unificado para configuração do SIGESCON
#
# Este script substitui reset_clean.sh, reset_database.sh e reset_examples.sh
# Oferece duas opções:
# 1. Setup Básico - apenas dados essenciais
# 2. Setup com Dados de Teste - dados essenciais + exemplos completos

set -e  # Sair se houver erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para exibir banner
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    SIGESCON - SETUP DO SISTEMA              ║"
    echo "║                  Sistema de Gestão de Contratos             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Função para exibir menu
show_menu() {
    echo -e "${YELLOW}Escolha uma opção:${NC}"
    echo ""
    echo -e "${GREEN}1) Setup Básico${NC}"
    echo "   • Reseta o banco de dados"
    echo "   • Insere dados essenciais para funcionamento"
    echo "   • Usuário admin, perfis, status, modalidades"
    echo ""
    echo -e "${BLUE}2) Setup com Dados de Teste${NC}"
    echo "   • Inclui tudo do Setup Básico"
    echo "   • Usuários de teste (fiscal, gestor)"
    echo "   • Contratos de exemplo completos"
    echo "   • Pendências em diferentes status"
    echo "   • Relatórios fiscais de exemplo"
    echo "   • Dados para demonstração/desenvolvimento"
    echo ""
    echo -e "${RED}3) Sair${NC}"
    echo ""
}

# Função para verificar pré-requisitos
check_prerequisites() {
    echo -e "${YELLOW}🔍 Verificando pré-requisitos...${NC}"

    # Verifica se está no diretório correto
    if [ ! -f "app/main.py" ]; then
        echo -e "${RED}❌ Execute este script a partir do diretório raiz do projeto backend${NC}"
        exit 1
    fi

    # Verifica se o ambiente virtual está ativo
    if [ -z "$VIRTUAL_ENV" ]; then
        echo -e "${YELLOW}⚠️  Ambiente virtual não detectado. Ativando...${NC}"
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            echo -e "${GREEN}✅ Ambiente virtual ativado${NC}"
        else
            echo -e "${RED}❌ Ambiente virtual .venv não encontrado${NC}"
            echo "Execute: python -m venv .venv && source .venv/bin/activate && pip install -e ."
            exit 1
        fi
    fi

    # Verifica se o arquivo .env existe
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ Arquivo .env não encontrado${NC}"
        echo "Crie um arquivo .env com as configurações do banco"
        exit 1
    fi

    # Carrega variáveis do .env
    export $(grep -v '^#' .env | xargs)

    echo -e "${GREEN}✅ Todos os pré-requisitos atendidos${NC}"
    echo ""
}

# Função para confirmar operação
confirm_operation() {
    local operation_type="$1"

    echo -e "${RED}⚠️  ATENÇÃO: Todos os dados do banco serão APAGADOS!${NC}"
    echo -e "${YELLOW}📋 Configurações:${NC}"
    echo "   • Banco: ${DATABASE_URL:-Local}"
    echo "   • Admin: ${ADMIN_EMAIL:-admin@sigescon.gov.br}"
    echo "   • Operação: $operation_type"
    echo ""

    read -p "$(echo -e ${YELLOW}Continuar? \(s/N\): ${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${RED}❌ Operação cancelada${NC}"
        exit 0
    fi
}

# Função para setup básico
setup_basico() {
    echo -e "${GREEN}🚀 Iniciando Setup Básico...${NC}"
    echo ""

    confirm_operation "Setup Básico (apenas dados essenciais)"

    echo -e "${CYAN}🔄 Executando reset e inserção de dados básicos...${NC}"

    # Criar script Python temporário para setup básico
    cat > /tmp/setup_basico.py << 'EOF'
import asyncio
import asyncpg
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# Função para hash de senha (simplificada)
def get_password_hash(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def setup_basico():
    """Setup básico - apenas dados essenciais"""
    print("🔄 Conectando ao banco de dados...")

    # Conexão com banco
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada no .env")
        return

    conn = await asyncpg.connect(database_url)

    try:
        print("🗑️  Limpando banco de dados...")

        # Limpar tabelas (ordem importante por causa das FKs)
        tables_to_clear = [
            'usuario_perfil', 'relatoriofiscal', 'arquivo', 'pendenciarelatorio',
            'contrato', 'usuario', 'contratado',
            'statuspendencia', 'statusrelatorio', 'status', 'modalidade', 'perfil'
        ]

        for table in tables_to_clear:
            await conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")

        print("✅ Banco limpo com sucesso")

        print("📊 Inserindo dados básicos...")

        # 1. Perfis
        perfis = [
            (1, 'Administrador'),
            (2, 'Gestor'),
            (3, 'Fiscal')
        ]

        await conn.executemany(
            "INSERT INTO perfil (id, nome) VALUES ($1, $2)",
            perfis
        )

        # 2. Status de Contrato
        status_contrato = [
            (1, 'Ativo'),
            (2, 'Suspenso'),
            (3, 'Encerrado'),
            (4, 'Cancelado')
        ]

        await conn.executemany(
            "INSERT INTO status (id, nome) VALUES ($1, $2)",
            status_contrato
        )

        # 3. Status de Pendência
        status_pendencia = [
            (1, 'Pendente'),
            (2, 'Concluída'),
            (3, 'Cancelada'),
            (4, 'Aguardando Análise')
        ]

        await conn.executemany(
            "INSERT INTO statuspendencia (id, nome) VALUES ($1, $2)",
            status_pendencia
        )

        # 4. Status de Relatório
        status_relatorio = [
            (1, 'Pendente de Análise'),
            (2, 'Aprovado'),
            (3, 'Rejeitado com Pendência')
        ]

        await conn.executemany(
            "INSERT INTO statusrelatorio (id, nome) VALUES ($1, $2)",
            status_relatorio
        )

        # 5. Modalidades
        modalidades = [
            'Pregão Eletrônico',
            'Pregão Presencial',
            'Concorrência',
            'Tomada de Preços',
            'Convite',
            'Concurso',
            'Leilão',
            'Dispensa de Licitação',
            'Inexigibilidade de Licitação'
        ]

        await conn.executemany(
            "INSERT INTO modalidade (nome) VALUES ($1)",
            [(modalidade,) for modalidade in modalidades]
        )

        print("✅ Dados básicos inseridos")

        # 6. Usuário Administrador
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@sigescon.gov.br')
        admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@123')

        print(f"👤 Criando usuário administrador: {admin_email}")

        admin_user_id = await conn.fetchval(
            """
            INSERT INTO usuario (nome, email, cpf, senha_hash, ativo, created_at, updated_at)
            VALUES ($1, $2, $3, $4, TRUE, NOW(), NOW())
            RETURNING id
            """,
            'Administrador do Sistema',
            admin_email,
            '00000000000',
            get_password_hash(admin_password)
        )

        # Conceder perfil Administrador
        await conn.execute(
            """
            INSERT INTO usuario_perfil (usuario_id, perfil_id, concedido_por_usuario_id, ativo, data_concessao)
            VALUES ($1, 1, $1, TRUE, NOW())
            """,
            admin_user_id
        )

        # Sincronizar sequências
        await conn.execute("SELECT setval(pg_get_serial_sequence('perfil', 'id'), (SELECT MAX(id) FROM perfil))")
        await conn.execute("SELECT setval(pg_get_serial_sequence('status', 'id'), (SELECT MAX(id) FROM status))")
        await conn.execute("SELECT setval(pg_get_serial_sequence('statuspendencia', 'id'), (SELECT MAX(id) FROM statuspendencia))")
        await conn.execute("SELECT setval(pg_get_serial_sequence('statusrelatorio', 'id'), (SELECT MAX(id) FROM statusrelatorio))")

        print("✅ Usuário administrador criado")
        print("✅ Setup básico concluído com sucesso!")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_basico())
EOF

    # Executar setup básico
    python /tmp/setup_basico.py

    # Limpar arquivo temporário
    rm /tmp/setup_basico.py

    echo ""
    echo -e "${GREEN}✅ Setup Básico concluído com sucesso!${NC}"
    echo -e "${CYAN}🔗 Acesse: http://localhost:8000/docs${NC}"
    echo -e "${YELLOW}👤 Login: ${ADMIN_EMAIL:-admin@sigescon.gov.br} / ${ADMIN_PASSWORD:-Admin@123}${NC}"
}

# Função para setup com dados de teste
setup_com_dados_teste() {
    echo -e "${BLUE}🚀 Iniciando Setup com Dados de Teste...${NC}"
    echo ""

    confirm_operation "Setup Completo (dados básicos + exemplos de teste)"

    # Primeiro executa o setup básico
    echo -e "${CYAN}📋 Etapa 1/2: Executando setup básico...${NC}"

    # Criar script Python para setup completo
    cat > /tmp/setup_completo.py << 'EOF'
import asyncio
import asyncpg
import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
import random
import string

load_dotenv()

def get_password_hash(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def generate_cpf():
    """Gera CPF válido para testes"""
    return ''.join([str(random.randint(0, 9)) for _ in range(11)])

def generate_cnpj():
    """Gera CNPJ válido para testes"""
    return ''.join([str(random.randint(0, 9)) for _ in range(14)])

async def setup_completo():
    """Setup completo - dados básicos + exemplos"""
    print("🔄 Conectando ao banco de dados...")

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada no .env")
        return

    conn = await asyncpg.connect(database_url)

    try:
        print("🗑️  Limpando banco de dados...")

        # Limpar tabelas
        tables_to_clear = [
            'usuario_perfil', 'relatoriofiscal', 'arquivo', 'pendenciarelatorio',
            'contrato', 'usuario', 'contratado',
            'statuspendencia', 'statusrelatorio', 'status', 'modalidade', 'perfil'
        ]

        for table in tables_to_clear:
            await conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")

        print("✅ Banco limpo com sucesso")

        # === DADOS BÁSICOS (mesmo do setup básico) ===
        print("📊 Inserindo dados básicos...")

        # Perfis
        perfis = [
            (1, 'Administrador'),
            (2, 'Gestor'),
            (3, 'Fiscal')
        ]
        await conn.executemany("INSERT INTO perfil (id, nome) VALUES ($1, $2)", perfis)

        # Status de Contrato
        status_contrato = [(1, 'Ativo'), (2, 'Suspenso'), (3, 'Encerrado'), (4, 'Cancelado')]
        await conn.executemany("INSERT INTO status (id, nome) VALUES ($1, $2)", status_contrato)

        # Status de Pendência
        status_pendencia = [(1, 'Pendente'), (2, 'Concluída'), (3, 'Cancelada'), (4, 'Aguardando Análise')]
        await conn.executemany("INSERT INTO statuspendencia (id, nome) VALUES ($1, $2)", status_pendencia)

        # Status de Relatório
        status_relatorio = [(1, 'Pendente de Análise'), (2, 'Aprovado'), (3, 'Rejeitado com Pendência')]
        await conn.executemany("INSERT INTO statusrelatorio (id, nome) VALUES ($1, $2)", status_relatorio)

        # Modalidades
        modalidades = [
            'Pregão Eletrônico', 'Pregão Presencial', 'Concorrência', 'Tomada de Preços',
            'Convite', 'Concurso', 'Leilão', 'Dispensa de Licitação', 'Inexigibilidade de Licitação'
        ]
        await conn.executemany("INSERT INTO modalidade (nome) VALUES ($1)", [(m,) for m in modalidades])

        # === USUÁRIO ADMINISTRADOR ===
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@sigescon.gov.br')
        admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@123')

        admin_user_id = await conn.fetchval(
            """INSERT INTO usuario (nome, email, cpf, senha_hash, ativo, created_at, updated_at)
               VALUES ($1, $2, $3, $4, TRUE, NOW(), NOW()) RETURNING id""",
            'Administrador do Sistema', admin_email, '00000000000', get_password_hash(admin_password)
        )

        await conn.execute(
            """INSERT INTO usuario_perfil (usuario_id, perfil_id, concedido_por_usuario_id, ativo, data_concessao)
               VALUES ($1, 1, $1, TRUE, NOW())""", admin_user_id
        )

        print("✅ Dados básicos inseridos")

        # === DADOS DE TESTE ===
        print("🧪 Inserindo dados de teste...")

        # Usuários de teste
        print("👥 Criando usuários de teste...")

        # Fiscal 1
        fiscal1_id = await conn.fetchval(
            """INSERT INTO usuario (nome, email, cpf, senha_hash, ativo, created_at, updated_at)
               VALUES ($1, $2, $3, $4, TRUE, NOW(), NOW()) RETURNING id""",
            'João Silva Fiscal', 'joao.fiscal@sigescon.gov.br', generate_cpf(), get_password_hash('Fiscal@123')
        )
        await conn.execute(
            """INSERT INTO usuario_perfil (usuario_id, perfil_id, concedido_por_usuario_id, ativo, data_concessao)
               VALUES ($1, 3, $2, TRUE, NOW())""", fiscal1_id, admin_user_id
        )

        # Fiscal 2
        fiscal2_id = await conn.fetchval(
            """INSERT INTO usuario (nome, email, cpf, senha_hash, ativo, created_at, updated_at)
               VALUES ($1, $2, $3, $4, TRUE, NOW(), NOW()) RETURNING id""",
            'Maria Santos Fiscal', 'maria.fiscal@sigescon.gov.br', generate_cpf(), get_password_hash('Fiscal@123')
        )
        await conn.execute(
            """INSERT INTO usuario_perfil (usuario_id, perfil_id, concedido_por_usuario_id, ativo, data_concessao)
               VALUES ($1, 3, $2, TRUE, NOW())""", fiscal2_id, admin_user_id
        )

        # Gestor
        gestor_id = await conn.fetchval(
            """INSERT INTO usuario (nome, email, cpf, senha_hash, ativo, created_at, updated_at)
               VALUES ($1, $2, $3, $4, TRUE, NOW(), NOW()) RETURNING id""",
            'Carlos Gestor Silva', 'carlos.gestor@sigescon.gov.br', generate_cpf(), get_password_hash('Gestor@123')
        )
        await conn.execute(
            """INSERT INTO usuario_perfil (usuario_id, perfil_id, concedido_por_usuario_id, ativo, data_concessao)
               VALUES ($1, 2, $2, TRUE, NOW())""", gestor_id, admin_user_id
        )

        print("✅ Usuários de teste criados")

        # Contratados de teste
        print("🏢 Criando contratados de teste...")

        contratados_data = [
            ('Empresa ABC Ltda', 'contato@empresaabc.com', generate_cnpj()),
            ('Tecnologia XYZ S.A.', 'admin@tecnologiaxyz.com', generate_cnpj()),
            ('Serviços DEF Eireli', 'comercial@servicosdef.com', generate_cnpj())
        ]

        contratado_ids = []
        for nome, email, cnpj in contratados_data:
            contratado_id = await conn.fetchval(
                """INSERT INTO contratado (nome, email, cnpj, ativo, created_at, updated_at)
                   VALUES ($1, $2, $3, TRUE, NOW(), NOW()) RETURNING id""",
                nome, email, cnpj
            )
            contratado_ids.append(contratado_id)

        print("✅ Contratados de teste criados")

        # Contratos de teste
        print("📋 Criando contratos de teste...")

        contratos_data = [
            {
                'nr_contrato': 'PGE-001/2025',
                'objeto': 'Prestação de serviços de desenvolvimento de software',
                'valor': 150000.00,
                'fiscal_id': fiscal1_id,
                'contratado_id': contratado_ids[0]
            },
            {
                'nr_contrato': 'PGE-002/2025',
                'objeto': 'Fornecimento de equipamentos de informática',
                'valor': 85000.00,
                'fiscal_id': fiscal2_id,
                'contratado_id': contratado_ids[1]
            },
            {
                'nr_contrato': 'PGE-003/2025',
                'objeto': 'Serviços de manutenção predial',
                'valor': 120000.00,
                'fiscal_id': fiscal1_id,
                'contratado_id': contratado_ids[2]
            }
        ]

        contrato_ids = []
        for contrato in contratos_data:
            contrato_id = await conn.fetchval(
                """INSERT INTO contrato (nr_contrato, objeto, data_inicio, data_fim,
                                      valor_global, fiscal_id, gestor_id, contratado_id, modalidade_id, status_id,
                                      ativo, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 1, 1, TRUE, NOW(), NOW()) RETURNING id""",
                contrato['nr_contrato'], contrato['objeto'],
                date(2025, 2, 1), date(2025, 12, 31),
                contrato['valor'], contrato['fiscal_id'], gestor_id,
                contrato['contratado_id']
            )
            contrato_ids.append(contrato_id)

        print("✅ Contratos de teste criados")

        # Pendências de teste (uma para cada status)
        print("📝 Criando pendências de teste...")

        hoje = datetime.now().date()
        data_vencida = date(2025, 8, 20)  # 20/08/2025
        data_futura = hoje + timedelta(days=15)  # 15 dias no futuro

        # Para cada contrato, criar pendências em diferentes status
        for i, contrato_id in enumerate(contrato_ids):
            fiscal_id = fiscal1_id if i % 2 == 0 else fiscal2_id

            # Pendência vencida (Pendente)
            pendencia_vencida_id = await conn.fetchval(
                """INSERT INTO pendenciarelatorio (contrato_id, descricao, data_prazo, status_pendencia_id,
                                                  criado_por_usuario_id, created_at, updated_at)
                   VALUES ($1, $2, $3, 1, $4, NOW(), NOW()) RETURNING id""",
                contrato_id, f'Relatório mensal vencido - Contrato {i+1}', data_vencida, admin_user_id
            )

            # Pendência futura (Pendente)
            pendencia_futura_id = await conn.fetchval(
                """INSERT INTO pendenciarelatorio (contrato_id, descricao, data_prazo, status_pendencia_id,
                                                  criado_por_usuario_id, created_at, updated_at)
                   VALUES ($1, $2, $3, 1, $4, NOW(), NOW()) RETURNING id""",
                contrato_id, f'Relatório mensal próximo - Contrato {i+1}', data_futura, admin_user_id
            )

            # Pendência aguardando análise (com relatório já enviado)
            pendencia_analise_id = await conn.fetchval(
                """INSERT INTO pendenciarelatorio (contrato_id, descricao, data_prazo, status_pendencia_id,
                                                  criado_por_usuario_id, created_at, updated_at)
                   VALUES ($1, $2, $3, 4, $4, NOW(), NOW()) RETURNING id""",
                contrato_id, f'Relatório aguardando análise - Contrato {i+1}', data_futura, admin_user_id
            )

            # Pendência concluída
            pendencia_concluida_id = await conn.fetchval(
                """INSERT INTO pendenciarelatorio (contrato_id, descricao, data_prazo, status_pendencia_id,
                                                  criado_por_usuario_id, created_at, updated_at)
                   VALUES ($1, $2, $3, 2, $4, NOW(), NOW()) RETURNING id""",
                contrato_id, f'Relatório concluído - Contrato {i+1}', data_futura, admin_user_id
            )

            # Criar arquivo de exemplo para pendência aguardando análise
            arquivo_id = await conn.fetchval(
                """INSERT INTO arquivo (nome_arquivo, caminho_arquivo, tipo_mime, tamanho_bytes,
                                      contrato_id, created_at)
                   VALUES ($1, $2, $3, $4, $5, NOW()) RETURNING id""",
                f'relatorio_exemplo_contrato_{i+1}.pdf',
                f'/uploads/contratos/{contrato_id}/relatorio_exemplo_contrato_{i+1}.pdf',
                'application/pdf', 2048, contrato_id
            )

            # Criar relatório para pendência aguardando análise
            await conn.execute(
                """INSERT INTO relatoriofiscal (contrato_id, arquivo_id, status_id, titulo,
                                               pendencia_id, fiscal_usuario_id, created_at, updated_at)
                   VALUES ($1, $2, 1, $3, $4, $5, NOW(), NOW())""",
                contrato_id, arquivo_id, f'Relatório Mensal - Contrato {i+1}', pendencia_analise_id, fiscal_id
            )

        print("✅ Pendências de teste criadas")

        # Sincronizar sequências
        await conn.execute("SELECT setval(pg_get_serial_sequence('perfil', 'id'), (SELECT MAX(id) FROM perfil))")
        await conn.execute("SELECT setval(pg_get_serial_sequence('status', 'id'), (SELECT MAX(id) FROM status))")
        await conn.execute("SELECT setval(pg_get_serial_sequence('statuspendencia', 'id'), (SELECT MAX(id) FROM statuspendencia))")
        await conn.execute("SELECT setval(pg_get_serial_sequence('statusrelatorio', 'id'), (SELECT MAX(id) FROM statusrelatorio))")

        print("✅ Setup completo concluído com sucesso!")

        # Exibir resumo
        print("\n" + "="*60)
        print("📊 RESUMO DOS DADOS INSERIDOS:")
        print("="*60)
        print("👤 Usuários:")
        print(f"   • Admin: {admin_email}")
        print("   • João Silva Fiscal: joao.fiscal@sigescon.gov.br")
        print("   • Maria Santos Fiscal: maria.fiscal@sigescon.gov.br")
        print("   • Carlos Gestor Silva: carlos.gestor@sigescon.gov.br")
        print("")
        print("📋 Contratos: 3 contratos de exemplo")
        print("📝 Pendências: 12 pendências (4 por contrato)")
        print("   • Vencidas (20/08/2025)")
        print("   • Futuras (15 dias no futuro)")
        print("   • Aguardando análise")
        print("   • Concluídas")
        print("🏢 Contratados: 3 empresas de exemplo")
        print("="*60)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_completo())
EOF

    echo -e "${CYAN}🔄 Executando setup completo...${NC}"
    python /tmp/setup_completo.py

    # Limpar arquivo temporário
    rm /tmp/setup_completo.py

    echo ""
    echo -e "${BLUE}✅ Setup com Dados de Teste concluído com sucesso!${NC}"
    echo -e "${CYAN}🔗 Acesse: http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}👤 Usuários de Login:${NC}"
    echo -e "   Admin: ${ADMIN_EMAIL:-admin@sigescon.gov.br} / ${ADMIN_PASSWORD:-Admin@123}"
    echo -e "   Fiscal 1: joao.fiscal@sigescon.gov.br / Fiscal@123"
    echo -e "   Fiscal 2: maria.fiscal@sigescon.gov.br / Fiscal@123"
    echo -e "   Gestor: carlos.gestor@sigescon.gov.br / Gestor@123"
}

# Função principal
main() {
    show_banner
    check_prerequisites

    while true; do
        show_menu
        read -p "$(echo -e ${YELLOW}Digite sua opção \(1-3\): ${NC})" choice
        echo

        case $choice in
            1)
                setup_basico
                break
                ;;
            2)
                setup_com_dados_teste
                break
                ;;
            3)
                echo -e "${YELLOW}👋 Saindo...${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Opção inválida. Tente novamente.${NC}"
                echo
                ;;
        esac
    done
}

# Executar função principal
main "$@"