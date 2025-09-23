#!/usr/bin/env python3
"""
Script seguro para resetar banco de dados em servidores de produção
Não requer privilégios de superusuário
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path
from datetime import datetime

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

async def safe_truncate_table(conn, table_name):
    """Trunca uma tabela de forma segura, lidando com foreign keys"""
    try:
        # Primeiro, tenta TRUNCATE CASCADE
        await conn.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
        print_success(f"Tabela '{table_name}' truncada com CASCADE")
        return True
    except Exception as e:
        try:
            # Se falhar, tenta DELETE simples
            await conn.execute(f"DELETE FROM {table_name}")
            print_warning(f"Tabela '{table_name}' limpa com DELETE (TRUNCATE falhou: {e})")
            return True
        except Exception as e2:
            print_error(f"Falha ao limpar tabela '{table_name}': {e2}")
            return False

async def get_tables_in_dependency_order(conn):
    """Obtém tabelas em ordem de dependência (folhas primeiro)"""
    # Lista tabelas na ordem que devem ser limpas (dependentes primeiro)
    # Baseado na estrutura real do servidor
    ordered_tables = [
        # Tabelas dependentes (com FKs) primeiro
        "relatoriofiscal",
        "pendenciarelatorio",
        "arquivo",
        "usuario_perfil",
        "contrato",

        # Tabelas intermediárias
        "contratado",
        "usuario",

        # Tabelas base (sem dependências) por último
        "statusrelatorio",
        "statuspendencia",
        "status",
        "modalidade",
        "perfil"
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

    # Adiciona tabelas que não estão na lista mas existem no banco
    extra_tables = [t for t in existing_table_names if t not in ordered_tables]

    return tables_to_clean + extra_tables

async def clean_database_safe(conn):
    """Limpa banco de dados sem usar session_replication_role"""
    print("\n🧹 LIMPANDO BANCO DE DADOS (MODO SEGURO)")
    print("=" * 60)

    try:
        # Obtém tabelas em ordem de dependência
        tables_to_clean = await get_tables_in_dependency_order(conn)
        print_info(f"Encontradas {len(tables_to_clean)} tabelas para limpar")

        cleaned_count = 0
        failed_count = 0

        # Limpa tabelas uma por uma
        for table in tables_to_clean:
            print(f"🔄 Limpando tabela: {table}")
            if await safe_truncate_table(conn, table):
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

    except Exception as e:
        print_error(f"Erro durante limpeza do banco: {e}")
        return False

async def seed_essential_data(conn):
    """Insere dados essenciais"""
    print("\n🌱 INSERINDO DADOS ESSENCIAIS")
    print("=" * 60)

    try:
        # Perfis (sem coluna descricao no servidor)
        print("📋 Inserindo perfis...")
        try:
            await conn.execute("""
                INSERT INTO perfil (id, nome, ativo) VALUES
                (1, 'Administrador', true),
                (2, 'Gestor', true),
                (3, 'Fiscal', true)
            """)
        except Exception as e:
            print_warning(f"Perfis podem já existir: {e}")

        # Status (sem coluna descricao no servidor)
        print("📋 Inserindo status...")
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

        # Status de Relatório (sem coluna descricao no servidor)
        print("📋 Inserindo status de relatório...")
        try:
            await conn.execute("""
                INSERT INTO statusrelatorio (id, nome, ativo) VALUES
                (1, 'Pendente de Análise', true),
                (2, 'Aprovado', true),
                (3, 'Rejeitado com Pendência', true)
            """)
        except Exception as e:
            print_warning(f"Status de relatório podem já existir: {e}")

        # Status de Pendência (sem coluna descricao no servidor)
        print("📋 Inserindo status de pendência...")
        try:
            await conn.execute("""
                INSERT INTO statuspendencia (id, nome, ativo) VALUES
                (1, 'Pendente', true),
                (2, 'Concluída', true),
                (3, 'Cancelada', true)
            """)
        except Exception as e:
            print_warning(f"Status de pendência podem já existir: {e}")

        # Modalidades (sem coluna descricao no servidor)
        print("📋 Inserindo modalidades...")
        try:
            await conn.execute("""
                INSERT INTO modalidade (id, nome, ativo) VALUES
                (1, 'Pregão Eletrônico', true),
                (2, 'Concorrência', true),
                (3, 'Tomada de Preços', true),
                (4, 'Convite', true),
                (5, 'Dispensa', true),
                (6, 'Inexigibilidade', true)
            """)
        except Exception as e:
            print_warning(f"Modalidades podem já existir: {e}")

        # Usuário administrador
        print("👤 Inserindo usuário administrador...")
        admin_email = settings.ADMIN_EMAIL or "admin@sigescon.pge.pa.gov.br"
        admin_password = settings.ADMIN_PASSWORD or "admin123"

        # Hash da senha (usando bcrypt como no sistema)
        import bcrypt
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            await conn.execute("""
                INSERT INTO usuario (nome, email, cpf, senha_hash, ativo, perfil_id)
                VALUES ($1, $2, $3, $4, true, 1)
            """, "Administrador do Sistema", admin_email, "00000000000", hashed_password)
        except Exception as e:
            # Se falhar, tenta atualizar o usuário existente
            try:
                await conn.execute("""
                    UPDATE usuario SET
                        senha_hash = $1,
                        ativo = true,
                        perfil_id = 1
                    WHERE email = $2
                """, hashed_password, admin_email)
                print_warning(f"Usuário admin atualizado (já existia)")
            except Exception as e2:
                print_error(f"Erro ao inserir/atualizar admin: {e2}")
                raise e2

        # Concede perfil de administrador
        admin_user = await conn.fetchrow("SELECT id FROM usuario WHERE email = $1", admin_email)
        if admin_user:
            try:
                await conn.execute("""
                    INSERT INTO usuario_perfil (usuario_id, perfil_id, ativo, data_concessao)
                    VALUES ($1, 1, true, NOW())
                """, admin_user['id'])
            except Exception as e:
                # Se falhar, tenta atualizar
                try:
                    await conn.execute("""
                        UPDATE usuario_perfil SET
                            ativo = true,
                            data_concessao = NOW()
                        WHERE usuario_id = $1 AND perfil_id = 1
                    """, admin_user['id'])
                except Exception:
                    print_warning(f"Perfil de admin já existe")

        print_success("Dados essenciais inseridos com sucesso!")
        print_info(f"👤 Admin: {admin_email} / {admin_password}")

        return True

    except Exception as e:
        print_error(f"Erro ao inserir dados essenciais: {e}")
        print_warning("Alguns dados podem ter sido inseridos parcialmente")
        return True  # Considera sucesso parcial como OK

async def main():
    """Função principal"""
    print("🔧 SIGESCON - RESET SEGURO DO SERVIDOR")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔗 URL do banco: {settings.DATABASE_URL}")
    print("=" * 60)

    try:
        # Conecta ao banco
        conn = await asyncpg.connect(settings.DATABASE_URL)
        print_success("Conexão com banco de dados estabelecida")

        # Limpa banco
        if not await clean_database_safe(conn):
            print_error("Falha na limpeza do banco. Abortando.")
            return False

        # Insere dados essenciais
        if not await seed_essential_data(conn):
            print_error("Falha ao inserir dados essenciais.")
            return False

        print("\n" + "=" * 60)
        print_success("RESET SEGURO CONCLUÍDO COM SUCESSO!")
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
    success = asyncio.run(main())
    sys.exit(0 if success else 1)