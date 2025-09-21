#!/usr/bin/env python3
"""
Script universal para reset do banco de dados SIGESCON
Funciona tanto localmente (com schema novo) quanto no servidor (schema antigo)
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path
from datetime import datetime, date
import bcrypt

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def print_header(message):
    print(f"\n🚀 {message}")
    print("=" * 60)

async def detect_schema_type(conn):
    """Detecta se é schema local (novo) ou servidor (antigo)"""
    try:
        # Verifica se existe tabela 'usuarios' (local) ou 'usuario' (servidor)
        local_tables = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('usuarios', 'contratos', 'contratados')
        """)

        server_tables = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('usuario', 'contrato', 'contratado')
        """)

        if local_tables > 0:
            print_info("Schema detectado: LOCAL (tabelas no plural)")
            return "local"
        elif server_tables > 0:
            print_info("Schema detectado: SERVIDOR (tabelas no singular)")
            return "server"
        else:
            print_info("Schema vazio - assumindo LOCAL")
            return "local"

    except Exception as e:
        print_warning(f"Erro ao detectar schema, assumindo LOCAL: {e}")
        return "local"

async def safe_truncate_table(conn, table_name, use_superuser_mode=False):
    """Trunca uma tabela de forma segura"""
    try:
        if use_superuser_mode:
            # Método com privilégios de superusuário (desenvolvimento local)
            await conn.execute("SET session_replication_role = 'replica'")
            await conn.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
            await conn.execute("SET session_replication_role = 'origin'")
        else:
            # Método sem privilégios especiais (produção/servidor)
            await conn.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")

        print_success(f"Tabela '{table_name}' truncada com CASCADE")
        return True
    except Exception as e:
        try:
            # Fallback: DELETE simples
            await conn.execute(f"DELETE FROM {table_name}")
            print_warning(f"Tabela '{table_name}' limpa com DELETE (TRUNCATE falhou: {e})")
            return True
        except Exception as e2:
            print_error(f"Falha ao limpar tabela '{table_name}': {e2}")
            return False

async def clean_database(conn, schema_type):
    """Limpa banco de dados de forma universal"""
    print_header("LIMPANDO BANCO DE DADOS")

    # Define tabelas baseado no schema
    if schema_type == "local":
        ordered_tables = [
            "relatoriofiscal", "pendenciarelatorio", "arquivos", "usuario_perfil", "contratos",
            "pendencias", "relatorios", "contratados", "usuarios",
            "statusrelatorio", "statuspendencia", "status", "modalidade", "perfil"
        ]
    else:  # server
        ordered_tables = [
            "relatoriofiscal", "pendenciarelatorio", "arquivo", "usuario_perfil", "contrato",
            "contratado", "usuario",
            "statusrelatorio", "statuspendencia", "status", "modalidade", "perfil"
        ]

    # Verifica quais tabelas existem
    existing_tables = await conn.fetch("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    existing_table_names = [t['tablename'] for t in existing_tables]

    # Filtra apenas tabelas que existem
    tables_to_clean = [t for t in ordered_tables if t in existing_table_names]
    extra_tables = [t for t in existing_table_names if t not in ordered_tables]
    tables_to_clean.extend(extra_tables)

    print_info(f"Encontradas {len(tables_to_clean)} tabelas para limpar")

    # Tenta detectar se pode usar modo superusuário
    use_superuser_mode = False
    try:
        await conn.execute("SET session_replication_role = 'replica'")
        await conn.execute("SET session_replication_role = 'origin'")
        use_superuser_mode = True
        print_info("Modo superusuário disponível - usando método otimizado")
    except:
        print_info("Modo superusuário não disponível - usando método seguro")

    cleaned_count = 0
    failed_count = 0

    for table in tables_to_clean:
        print(f"🔄 Limpando tabela: {table}")
        if await safe_truncate_table(conn, table, use_superuser_mode):
            cleaned_count += 1
        else:
            failed_count += 1

    print(f"\n📊 RESULTADO DA LIMPEZA:")
    print_success(f"Tabelas limpas com sucesso: {cleaned_count}")
    if failed_count > 0:
        print_warning(f"Tabelas com erro: {failed_count}")
    else:
        print_success("Todas as tabelas foram limpas!")

    return True

async def seed_basic_data(conn, schema_type):
    """Insere dados básicos no formato correto para cada schema"""
    print_header("INSERINDO DADOS BÁSICOS")

    try:
        # Perfis
        print("📋 Inserindo perfis...")
        if schema_type == "local":
            await conn.execute("""
                INSERT INTO perfil (id, nome, descricao, ativo) VALUES
                (1, 'Administrador', 'Acesso total ao sistema', true),
                (2, 'Gestor', 'Gerencia contratos e equipes', true),
                (3, 'Fiscal', 'Fiscaliza contratos e envia relatórios', true)
                ON CONFLICT (id) DO NOTHING
            """)
        else:  # server
            try:
                await conn.execute("""
                    INSERT INTO perfil (id, nome, ativo) VALUES
                    (1, 'Administrador', true),
                    (2, 'Gestor', true),
                    (3, 'Fiscal', true)
                """)
            except Exception as e:
                print_warning(f"Perfis podem já existir: {e}")

        # Status
        print("📋 Inserindo status...")
        if schema_type == "local":
            await conn.execute("""
                INSERT INTO status (id, nome, descricao, ativo) VALUES
                (1, 'Ativo', 'Contrato em execução', true),
                (2, 'Suspenso', 'Contrato temporariamente suspenso', true),
                (3, 'Encerrado', 'Contrato finalizado', true),
                (4, 'Cancelado', 'Contrato cancelado', true)
                ON CONFLICT (id) DO NOTHING
            """)
        else:  # server
            try:
                await conn.execute("""
                    INSERT INTO status (id, nome, ativo) VALUES
                    (1, 'Ativo', true),
                    (2, 'Suspenso', true),
                    (3, 'Encerrado', true),
                    (4, 'Cancelado', true)
                """)
            except Exception as e:
                print_warning(f"Status podem já existir: {e}")

        # Status de Relatório
        print("📋 Inserindo status de relatório...")
        if schema_type == "local":
            await conn.execute("""
                INSERT INTO status_relatorio (id, nome, descricao) VALUES
                (1, 'Pendente de Análise', 'Aguardando análise do administrador'),
                (2, 'Aprovado', 'Relatório aprovado'),
                (3, 'Rejeitado com Pendência', 'Relatório rejeitado, fiscal deve corrigir')
                ON CONFLICT (id) DO NOTHING
            """)
        else:  # server
            try:
                await conn.execute("""
                    INSERT INTO statusrelatorio (id, nome, ativo) VALUES
                    (1, 'Pendente de Análise', true),
                    (2, 'Aprovado', true),
                    (3, 'Rejeitado com Pendência', true)
                """)
            except Exception as e:
                print_warning(f"Status de relatório podem já existir: {e}")

        # Status de Pendência
        print("📋 Inserindo status de pendência...")
        if schema_type == "local":
            await conn.execute("""
                INSERT INTO status_pendencia (id, nome, descricao) VALUES
                (1, 'Pendente', 'Aguardando ação do fiscal'),
                (2, 'Concluída', 'Pendência resolvida'),
                (3, 'Cancelada', 'Pendência cancelada pelo administrador')
                ON CONFLICT (id) DO NOTHING
            """)
        else:  # server
            try:
                await conn.execute("""
                    INSERT INTO statuspendencia (id, nome, ativo) VALUES
                    (1, 'Pendente', true),
                    (2, 'Concluída', true),
                    (3, 'Cancelada', true)
                """)
            except Exception as e:
                print_warning(f"Status de pendência podem já existir: {e}")

        # Modalidades
        print("📋 Inserindo modalidades...")
        if schema_type == "local":
            await conn.execute("""
                INSERT INTO modalidade (id, nome, descricao, ativo) VALUES
                (1, 'Pregão Eletrônico', 'Licitação eletrônica para bens e serviços comuns', true),
                (2, 'Concorrência', 'Modalidade para contratos de grande valor', true),
                (3, 'Tomada de Preços', 'Modalidade para contratos de valor médio', true),
                (4, 'Convite', 'Modalidade para contratos de pequeno valor', true),
                (5, 'Dispensa', 'Contratação por dispensa de licitação', true),
                (6, 'Inexigibilidade', 'Contratação por inexigibilidade de licitação', true),
                (7, 'Registro de Preços', 'Sistema de registro de preços', true),
                (8, 'Parceria Público-Privada', 'Concessão ou permissão de serviços', true)
                ON CONFLICT (id) DO NOTHING
            """)
        else:  # server
            try:
                await conn.execute("""
                    INSERT INTO modalidade (id, nome, ativo) VALUES
                    (1, 'Pregão Eletrônico', true),
                    (2, 'Concorrência', true),
                    (3, 'Tomada de Preços', true),
                    (4, 'Convite', true),
                    (5, 'Dispensa', true),
                    (6, 'Inexigibilidade', true),
                    (7, 'Registro de Preços', true),
                    (8, 'Parceria Público-Privada', true)
                """)
            except Exception as e:
                print_warning(f"Modalidades podem já existir: {e}")

        # Usuário administrador
        print("👤 Inserindo usuário administrador...")
        admin_email = settings.ADMIN_EMAIL or "admin@sigescon.pge.pa.gov.br"
        admin_password = settings.ADMIN_PASSWORD or "admin123"
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        users_table = "usuarios" if schema_type == "local" else "usuario"

        try:
            # Tenta inserir sem perfil_id (sistema de múltiplos perfis)
            try:
                await conn.execute(f"""
                    INSERT INTO {users_table} (nome, email, cpf, senha, ativo)
                    VALUES ($1, $2, $3, $4, true)
                    ON CONFLICT (email) DO UPDATE SET
                        senha = EXCLUDED.senha,
                        ativo = true
                """, "Administrador do Sistema", admin_email, "00000000000", hashed_password)
            except Exception as e:
                # Fallback: tenta com perfil_id ou sem ON CONFLICT
                if "ON CONFLICT" in str(e) or "conflict" in str(e).lower():
                    # Sem ON CONFLICT
                    try:
                        await conn.execute(f"""
                            INSERT INTO {users_table} (nome, email, cpf, senha, ativo)
                            VALUES ($1, $2, $3, $4, true)
                        """, "Administrador do Sistema", admin_email, "00000000000", hashed_password)
                    except Exception:
                        # Atualiza se já existe
                        await conn.execute(f"""
                            UPDATE {users_table} SET
                                senha = $1,
                                ativo = true
                            WHERE email = $2
                        """, hashed_password, admin_email)
                else:
                    raise e
        except Exception as e:
            print_error(f"Erro ao criar usuário admin: {e}")
            return False

        # Concede perfil de administrador via tabela usuario_perfil
        admin_user = await conn.fetchrow(f"SELECT id FROM {users_table} WHERE email = $1", admin_email)
        if admin_user:
            try:
                await conn.execute("""
                    INSERT INTO usuario_perfil (usuario_id, perfil_id, ativo, data_concessao)
                    VALUES ($1, 1, true, NOW())
                    ON CONFLICT (usuario_id, perfil_id) DO UPDATE SET
                        ativo = true,
                        data_concessao = NOW()
                """, admin_user['id'])
            except Exception as e:
                # Fallback sem ON CONFLICT
                try:
                    await conn.execute("""
                        INSERT INTO usuario_perfil (usuario_id, perfil_id, ativo, data_concessao)
                        VALUES ($1, 1, true, NOW())
                    """, admin_user['id'])
                except Exception:
                    # Já existe, atualiza
                    await conn.execute("""
                        UPDATE usuario_perfil SET
                            ativo = true,
                            data_concessao = NOW()
                        WHERE usuario_id = $1 AND perfil_id = 1
                    """, admin_user['id'])

        print_success("Dados básicos inseridos com sucesso!")
        print_info(f"👤 Admin: {admin_email} / {admin_password}")

        return True

    except Exception as e:
        print_error(f"Erro ao inserir dados básicos: {e}")
        return False

async def main(example_data=False):
    """Função principal"""
    mode_text = "COM DADOS DE EXEMPLO" if example_data else "APENAS DADOS BÁSICOS"
    print(f"🔧 SIGESCON - RESET UNIVERSAL ({mode_text})")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔗 URL do banco: {settings.DATABASE_URL}")
    print("=" * 60)

    try:
        # Conecta ao banco
        conn = await asyncpg.connect(settings.DATABASE_URL)
        print_success("Conexão com banco de dados estabelecida")

        # Detecta tipo de schema
        schema_type = await detect_schema_type(conn)

        # Limpa banco
        if not await clean_database(conn, schema_type):
            print_error("Falha na limpeza do banco. Abortando.")
            return False

        # Insere dados básicos
        if not await seed_basic_data(conn, schema_type):
            print_error("Falha ao inserir dados básicos.")
            return False

        if example_data:
            # Importa e executa seed de dados de exemplo
            try:
                from seed_example_data import seed_example_data
                if not await seed_example_data(conn, schema_type):
                    print_error("Falha ao inserir dados de exemplo.")
                    return False
            except ImportError:
                # Tenta path alternativo
                import sys
                from pathlib import Path
                sys.path.append(str(Path(__file__).parent))
                from seed_example_data import seed_example_data
                if not await seed_example_data(conn, schema_type):
                    print_error("Falha ao inserir dados de exemplo.")
                    return False

        print("\n" + "=" * 60)
        print_success(f"RESET UNIVERSAL CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"🔗 API: http://localhost:8000/docs")
        print(f"👤 Login: {settings.ADMIN_EMAIL} / {settings.ADMIN_PASSWORD}")

        return True

    except Exception as e:
        print_error(f"Erro fatal: {e}")
        return False
    finally:
        if 'conn' in locals():
            await conn.close()
            print_success("Conexão com banco encerrada")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Reset universal do banco SIGESCON')
    parser.add_argument('--examples', action='store_true',
                       help='Inclui dados de exemplo (contratos, pendências, etc.)')
    args = parser.parse_args()

    success = asyncio.run(main(example_data=args.examples))
    sys.exit(0 if success else 1)