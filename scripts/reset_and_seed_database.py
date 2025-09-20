#!/usr/bin/env python3
"""
Script para resetar e popular o banco de dados SIGESCON
Apaga todos os dados e reinsere dados essenciais para desenvolvimento/produção

Uso:
    python scripts/reset_and_seed_database.py

Variáveis de ambiente necessárias:
    DATABASE_URL ou individualmente:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any

# Adiciona o diretório raiz ao path para importar módulos do app
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.security import get_password_hash

# ============================================================================
# CONFIGURAÇÃO DOS DADOS DE SEED
# ============================================================================

# Dados essenciais para as tabelas de lookup
SEED_DATA = {
    'perfil': [
        'Administrador',
        'Gestor',
        'Fiscal'
    ],

    'modalidade': [
        'Pregão Eletrônico',
        'Pregão Presencial',
        'Concorrência',
        'Concurso',
        'Leilão',
        'Diálogo Competitivo',
        'Dispensa de Licitação',
        'Inexigibilidade de Licitação',
        'Credenciamento'
    ],

    'status': [
        'Vigente',
        'Encerrado',
        'Rescindido',
        'Suspenso',
        'Aguardando Publicação',
        'Em Execução',
        'Finalizado'
    ],

    'statusrelatorio': [
        'Pendente de Análise',
        'Aprovado',
        'Rejeitado com Pendência'
    ],

    'statuspendencia': [
        'Pendente',
        'Concluída',
        'Cancelada'
    ]
}

# Usuários padrão do sistema
DEFAULT_USERS = [
    {
        'nome': 'Administrador do Sistema',
        'email': settings.ADMIN_EMAIL or 'admin@sigescon.gov.br',
        'cpf': '11122233344',  # CPF válido
        'matricula': 'ADM001',
        'senha': settings.ADMIN_PASSWORD or 'admin123',
        'perfil': 'Administrador'
    },
    {
        'nome': 'João Silva - Gestor',
        'email': 'gestor@sigescon.gov.br',
        'cpf': '12345678901',  # CPF válido
        'matricula': 'GES001',
        'senha': 'gestor123',
        'perfil': 'Gestor'
    },
    {
        'nome': 'Maria Santos - Fiscal',
        'email': 'fiscal@sigescon.gov.br',
        'cpf': '98765432100',  # CPF válido
        'matricula': 'FIS001',
        'senha': 'fiscal123',
        'perfil': 'Fiscal'
    }
]

# Empresas/pessoas contratadas de exemplo
SAMPLE_CONTRATADOS = [
    {
        'nome': 'Tech Solutions Ltda',
        'cnpj': '12345678000199',
        'cpf': None,
        'telefone': '11999887766',
        'email': 'contato@techsolutions.com.br'
    },
    {
        'nome': 'Construtora ABC S.A.',
        'cnpj': '98765432000188',
        'cpf': None,
        'telefone': '11888776655',
        'email': 'obras@construtorabc.com.br'
    },
    {
        'nome': 'João Consultor MEI',
        'cnpj': None,
        'cpf': '33333333333',
        'telefone': '11777665544',
        'email': 'joao.consultor@email.com'
    }
]

# Contratos de exemplo
SAMPLE_CONTRATOS = [
    {
        'nr_contrato': 'CONT/2024/001',
        'objeto': 'Desenvolvimento de Sistema de Gestão de Contratos',
        'termos_contratuais': 'Desenvolvimento completo de sistema web para gestão de contratos governamentais incluindo módulos de usuários, contratos, relatórios e pendências.',
        'data_inicio': date(2024, 2, 1),
        'data_fim': date(2024, 12, 31),
        'valor_global': 250000.00,
        'contratado_nome': 'Tech Solutions Ltda',
        'modalidade_nome': 'Pregão Eletrônico',
        'status_nome': 'Vigente'
    },
    {
        'nr_contrato': 'CONT/2024/002',
        'objeto': 'Reforma do Prédio Administrativo',
        'termos_contratuais': 'Reforma completa do prédio administrativo incluindo pintura, elétrica, hidráulica e climatização.',
        'data_inicio': date(2024, 4, 1),
        'data_fim': date(2024, 8, 30),
        'valor_global': 180000.00,
        'contratado_nome': 'Construtora ABC S.A.',
        'modalidade_nome': 'Concorrência',
        'status_nome': 'Vigente'
    },
    {
        'nr_contrato': 'CONT/2024/003',
        'objeto': 'Consultoria em Gestão de Processos',
        'termos_contratuais': 'Consultoria especializada para mapeamento e otimização de processos administrativos.',
        'data_inicio': date(2024, 3, 1),
        'data_fim': date(2024, 6, 30),
        'valor_global': 45000.00,
        'contratado_nome': 'João Consultor MEI',
        'modalidade_nome': 'Dispensa de Licitação',
        'status_nome': 'Vigente'
    }
]

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def print_step(step: str):
    """Imprime uma etapa do processo com formatação"""
    print(f"\n{'='*60}")
    print(f"🔄 {step}")
    print(f"{'='*60}")

def print_success(message: str):
    """Imprime mensagem de sucesso"""
    print(f"✅ {message}")

def print_warning(message: str):
    """Imprime mensagem de aviso"""
    print(f"⚠️  {message}")

def print_error(message: str):
    """Imprime mensagem de erro"""
    print(f"❌ {message}")

async def get_database_connection() -> asyncpg.Connection:
    """Estabelece conexão com o banco de dados"""
    try:
        if settings.DATABASE_URL:
            conn = await asyncpg.connect(settings.DATABASE_URL)
        else:
            conn = await asyncpg.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5432)),
                database=os.getenv('DB_NAME', 'contratos'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'senha')
            )
        print_success("Conexão com banco de dados estabelecida")
        return conn
    except Exception as e:
        print_error(f"Erro ao conectar com banco de dados: {e}")
        raise

# ============================================================================
# FUNÇÕES DE LIMPEZA
# ============================================================================

async def truncate_all_tables(conn: asyncpg.Connection):
    """Remove todos os dados de todas as tabelas"""
    print_step("LIMPANDO BANCO DE DADOS")

    # Lista de tabelas na ordem de dependência (filhas primeiro)
    tables_to_truncate = [
        'relatoriofiscal',
        'pendenciarelatorio',
        'arquivo',
        'contrato',
        'contratado',
        'usuario_perfil',
        'usuario',
        'statusrelatorio',
        'statuspendencia',
        'status',
        'modalidade',
        'perfil'
    ]

    try:
        # Desabilita verificação de foreign keys temporariamente
        await conn.execute("SET session_replication_role = 'replica';")

        for table in tables_to_truncate:
            try:
                # Truncate com restart identity para resetar sequências
                await conn.execute(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE;')
                print_success(f"Tabela '{table}' limpa")
            except Exception as e:
                print_warning(f"Erro ao limpar tabela '{table}': {e}")

        # Reabilita verificação de foreign keys
        await conn.execute("SET session_replication_role = 'origin';")

        print_success("Todas as tabelas foram limpas com sucesso!")

    except Exception as e:
        print_error(f"Erro durante limpeza das tabelas: {e}")
        raise

# ============================================================================
# FUNÇÕES DE SEED
# ============================================================================

async def seed_lookup_tables(conn: asyncpg.Connection):
    """Popula tabelas de lookup com dados essenciais"""
    print_step("POPULANDO TABELAS DE LOOKUP")

    for table_name, values in SEED_DATA.items():
        try:
            # Insere cada valor
            for value in values:
                await conn.execute(
                    f'INSERT INTO "{table_name}" (nome) VALUES ($1)',
                    value
                )

            count = len(values)
            print_success(f"Tabela '{table_name}': {count} registros inseridos")

        except Exception as e:
            print_error(f"Erro ao popular tabela '{table_name}': {e}")
            raise

async def seed_admin_only(conn: asyncpg.Connection):
    """Cria apenas o usuário administrador (modo clean)"""
    print_step("CRIANDO USUÁRIO ADMINISTRADOR")

    admin_data = {
        'nome': 'Administrador do Sistema',
        'email': settings.ADMIN_EMAIL or 'admin@sigescon.gov.br',
        'cpf': '11122233344',  # CPF válido
        'matricula': 'ADM001',
        'senha': settings.ADMIN_PASSWORD or 'admin123',
        'perfil': 'Administrador'
    }

    try:
        # Busca o ID do perfil
        perfil_id = await conn.fetchval(
            'SELECT id FROM perfil WHERE nome = $1',
            admin_data['perfil']
        )

        if not perfil_id:
            print_error(f"Perfil '{admin_data['perfil']}' não encontrado")
            return

        # Hash da senha
        senha_hash = get_password_hash(admin_data['senha'])

        # Insere usuário (sem perfil_id no campo legacy)
        user_id = await conn.fetchval(
            '''
            INSERT INTO usuario (nome, email, cpf, matricula, senha)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            ''',
            admin_data['nome'],
            admin_data['email'],
            admin_data['cpf'],
            admin_data['matricula'],
            senha_hash
        )

        # Associa o perfil na tabela usuario_perfil
        await conn.execute(
            '''
            INSERT INTO usuario_perfil (usuario_id, perfil_id, concedido_por_usuario_id, ativo)
            VALUES ($1, $2, $1, TRUE)
            ''',
            user_id, perfil_id
        )

        print_success(f"Usuário criado: {admin_data['nome']} ({admin_data['email']}) - ID: {user_id}")

    except Exception as e:
        print_error(f"Erro ao criar usuário administrador: {e}")
        raise

async def seed_users(conn: asyncpg.Connection):
    """Cria usuários padrão do sistema"""
    print_step("CRIANDO USUÁRIOS PADRÃO")

    for user_data in DEFAULT_USERS:
        try:
            # Busca o ID do perfil
            perfil_id = await conn.fetchval(
                'SELECT id FROM perfil WHERE nome = $1',
                user_data['perfil']
            )

            if not perfil_id:
                print_error(f"Perfil '{user_data['perfil']}' não encontrado")
                continue

            # Hash da senha
            senha_hash = get_password_hash(user_data['senha'])

            # Insere usuário (sem perfil_id no campo legacy)
            user_id = await conn.fetchval(
                '''
                INSERT INTO usuario (nome, email, cpf, matricula, senha)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                ''',
                user_data['nome'],
                user_data['email'],
                user_data['cpf'],
                user_data['matricula'],
                senha_hash
            )

            # Associa o perfil na tabela usuario_perfil
            await conn.execute(
                '''
                INSERT INTO usuario_perfil (usuario_id, perfil_id, concedido_por_usuario_id, ativo)
                VALUES ($1, $2, $1, TRUE)
                ''',
                user_id, perfil_id
            )

            print_success(f"Usuário criado: {user_data['nome']} ({user_data['email']}) - ID: {user_id}")

        except Exception as e:
            print_error(f"Erro ao criar usuário {user_data['nome']}: {e}")
            raise

async def seed_contratados(conn: asyncpg.Connection):
    """Cria empresas/pessoas contratadas de exemplo"""
    print_step("CRIANDO CONTRATADOS DE EXEMPLO")

    for contratado_data in SAMPLE_CONTRATADOS:
        try:
            contratado_id = await conn.fetchval(
                '''
                INSERT INTO contratado (nome, cnpj, cpf, telefone, email)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                ''',
                contratado_data['nome'],
                contratado_data['cnpj'],
                contratado_data['cpf'],
                contratado_data['telefone'],
                contratado_data['email']
            )

            print_success(f"Contratado criado: {contratado_data['nome']} - ID: {contratado_id}")

        except Exception as e:
            print_error(f"Erro ao criar contratado {contratado_data['nome']}: {e}")
            raise

async def seed_contratos(conn: asyncpg.Connection):
    """Cria contratos de exemplo"""
    print_step("CRIANDO CONTRATOS DE EXEMPLO")

    # Busca usuários para associar como gestor/fiscal
    usuarios = await conn.fetch('SELECT id, nome FROM usuario ORDER BY id')
    gestor_id = None
    fiscal_id = None

    for user in usuarios:
        if 'Gestor' in user['nome']:
            gestor_id = user['id']
        elif 'Fiscal' in user['nome']:
            fiscal_id = user['id']

    for contrato_data in SAMPLE_CONTRATOS:
        try:
            # Busca IDs das tabelas relacionadas
            contratado_id = await conn.fetchval(
                'SELECT id FROM contratado WHERE nome = $1',
                contrato_data['contratado_nome']
            )

            modalidade_id = await conn.fetchval(
                'SELECT id FROM modalidade WHERE nome = $1',
                contrato_data['modalidade_nome']
            )

            status_id = await conn.fetchval(
                'SELECT id FROM status WHERE nome = $1',
                contrato_data['status_nome']
            )

            if not all([contratado_id, modalidade_id, status_id]):
                print_warning(f"Dados relacionados não encontrados para contrato {contrato_data['nr_contrato']}")
                continue

            # Insere contrato
            contrato_id = await conn.fetchval(
                '''
                INSERT INTO contrato (
                    nr_contrato, objeto, termos_contratuais, data_inicio, data_fim,
                    valor_global, contratado_id, modalidade_id, status_id, gestor_id, fiscal_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
                ''',
                contrato_data['nr_contrato'],
                contrato_data['objeto'],
                contrato_data['termos_contratuais'],
                contrato_data['data_inicio'],
                contrato_data['data_fim'],
                contrato_data['valor_global'],
                contratado_id,
                modalidade_id,
                status_id,
                gestor_id,
                fiscal_id
            )

            print_success(f"Contrato criado: {contrato_data['nr_contrato']} - ID: {contrato_id}")

        except Exception as e:
            print_error(f"Erro ao criar contrato {contrato_data['nr_contrato']}: {e}")
            raise

async def create_sample_pendencias(conn: asyncpg.Connection):
    """Cria algumas pendências de exemplo"""
    print_step("CRIANDO PENDÊNCIAS DE EXEMPLO")

    try:
        # Busca dados necessários
        contratos = await conn.fetch('SELECT id, nr_contrato FROM contrato LIMIT 2')
        admin_id = await conn.fetchval('SELECT id FROM usuario WHERE email = $1', settings.ADMIN_EMAIL or 'admin@sigescon.gov.br')
        status_pendente_id = await conn.fetchval('SELECT id FROM statuspendencia WHERE nome = $1', 'Pendente')

        if not all([contratos, admin_id, status_pendente_id]):
            print_warning("Dados necessários para pendências não encontrados")
            return

        sample_pendencias = [
            {
                'descricao': 'Enviar relatório mensal de acompanhamento - Janeiro/2024',
                'data_prazo': date(2024, 2, 10),
                'contrato_id': contratos[0]['id']
            },
            {
                'descricao': 'Relatório de execução física e financeira - 1º Trimestre',
                'data_prazo': date(2024, 4, 15),
                'contrato_id': contratos[1]['id'] if len(contratos) > 1 else contratos[0]['id']
            }
        ]

        for pendencia_data in sample_pendencias:
            pendencia_id = await conn.fetchval(
                '''
                INSERT INTO pendenciarelatorio (
                    descricao, data_prazo, status_pendencia_id,
                    contrato_id, criado_por_usuario_id
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                ''',
                pendencia_data['descricao'],
                pendencia_data['data_prazo'],
                status_pendente_id,
                pendencia_data['contrato_id'],
                admin_id
            )

            print_success(f"Pendência criada: {pendencia_data['descricao'][:50]}... - ID: {pendencia_id}")

    except Exception as e:
        print_error(f"Erro ao criar pendências: {e}")

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

async def reset_and_seed_database(clean_mode: bool = False):
    """Função principal que executa todo o processo

    Args:
        clean_mode: Se True, cria apenas dados essenciais (perfis, status, admin)
                   Se False, cria dados completos com exemplos
    """
    mode_text = "CLEAN (Apenas Essenciais)" if clean_mode else "COMPLETO (Com Exemplos)"
    print("\n" + "="*80)
    print(f"🚀 SIGESCON - RESET E SEED DO BANCO DE DADOS - {mode_text}")
    print("="*80)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🗄️  Banco: {settings.DATABASE_URL or 'Configuração local'}")
    print("="*80)

    conn = None
    try:
        # Conecta ao banco
        conn = await get_database_connection()

        # Etapa 1: Limpar todas as tabelas
        await truncate_all_tables(conn)

        # Etapa 2: Popular tabelas de lookup
        await seed_lookup_tables(conn)

        if clean_mode:
            # Modo Clean: Apenas admin
            await seed_admin_only(conn)
        else:
            # Modo Completo: Todos os dados de exemplo
            # Etapa 3: Criar usuários padrão
            await seed_users(conn)

            # Etapa 4: Criar contratados de exemplo
            await seed_contratados(conn)

            # Etapa 5: Criar contratos de exemplo
            await seed_contratos(conn)

            # Etapa 6: Criar pendências de exemplo
            await create_sample_pendencias(conn)

        # Resumo final
        print_step("RESUMO FINAL")

        # Conta registros criados
        counts = {}
        if clean_mode:
            tables = ['perfil', 'usuario', 'modalidade', 'status', 'statusrelatorio', 'statuspendencia']
        else:
            tables = ['perfil', 'usuario', 'contratado', 'modalidade', 'status', 'statusrelatorio', 'statuspendencia', 'contrato', 'pendenciarelatorio']

        for table in tables:
            count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table}"')
            counts[table] = count

        print("📊 Registros criados:")
        for table, count in counts.items():
            print(f"   • {table}: {count} registros")

        print_success("🎉 BANCO DE DADOS RESETADO E POPULADO COM SUCESSO!")
        print("\n📝 Credenciais de acesso:")
        print(f"   • Admin: {settings.ADMIN_EMAIL or 'admin@sigescon.gov.br'} / {settings.ADMIN_PASSWORD or 'admin123'}")

        if not clean_mode:
            print("   • Gestor: gestor@sigescon.gov.br / gestor123")
            print("   • Fiscal: fiscal@sigescon.gov.br / fiscal123")

        print(f"\n🚀 O sistema está pronto para uso {'(modo clean)' if clean_mode else '(com dados de exemplo)'}!")

    except Exception as e:
        print_error(f"Erro durante o processo: {e}")
        sys.exit(1)

    finally:
        if conn:
            await conn.close()
            print_success("Conexão com banco encerrada")

# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    # Verifica se as configurações estão disponíveis
    if not settings.DATABASE_URL and not all([
        os.getenv('DB_HOST'),
        os.getenv('DB_NAME'),
        os.getenv('DB_USER'),
        os.getenv('DB_PASSWORD')
    ]):
        print_error("❌ Configuração de banco de dados não encontrada!")
        print("Configure DATABASE_URL ou DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)

    # Verifica argumentos de linha de comando
    import argparse
    parser = argparse.ArgumentParser(description='Reset e seed do banco de dados SIGESCON')
    parser.add_argument('--clean', action='store_true',
                       help='Modo clean: cria apenas dados essenciais (perfis, status, admin)')
    parser.add_argument('--force', action='store_true',
                       help='Força execução sem confirmação (cuidado!)')
    args = parser.parse_args()

    # Confirma a operação (a menos que --force seja usado)
    if not args.force:
        mode_text = "CLEAN (apenas essenciais)" if args.clean else "COMPLETO (com exemplos)"
        print(f"⚠️  ATENÇÃO: Este script irá APAGAR TODOS OS DADOS do banco!")
        print(f"Modo selecionado: {mode_text}")
        confirm = input("Digite 'CONFIRMO' para continuar: ")

        if confirm != 'CONFIRMO':
            print("❌ Operação cancelada pelo usuário")
            sys.exit(0)

    # Executa o reset e seed
    asyncio.run(reset_and_seed_database(clean_mode=args.clean))