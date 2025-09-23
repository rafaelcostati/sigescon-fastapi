#!/usr/bin/env python3
"""
Script para popular banco com dados de exemplo completos
"""

import asyncpg
from datetime import datetime, date, timedelta
import bcrypt
import os

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def print_header(message):
    print(f"\n🌱 {message}")
    print("=" * 60)

async def seed_example_data(conn, schema_type):
    """Popula banco com dados de exemplo completos"""
    print_header("INSERINDO DADOS DE EXEMPLO")

    try:
        # Define nomes de tabelas baseado no schema
        users_table = "usuarios" if schema_type == "local" else "usuario"
        contracts_table = "contratos" if schema_type == "local" else "contrato"
        contractors_table = "contratados" if schema_type == "local" else "contratado"

        # 1. USUÁRIOS DE EXEMPLO
        print("👥 Criando usuários de exemplo...")

        usuarios_exemplo = [
            {
                "nome": "Maria Silva Santos",
                "email": "maria.silva@pge.pa.gov.br",
                "cpf": "12345678901",
                "perfis": [2]  # Gestor
            },
            {
                "nome": "João Carlos Oliveira",
                "email": "joao.oliveira@pge.pa.gov.br",
                "cpf": "23456789012",
                "perfis": [3]  # Fiscal
            },
            {
                "nome": "Ana Paula Costa",
                "email": "ana.costa@pge.pa.gov.br",
                "cpf": "34567890123",
                "perfis": [3]  # Fiscal
            },
            {
                "nome": "Carlos Eduardo Lima",
                "email": "carlos.lima@pge.pa.gov.br",
                "cpf": "45678901234",
                "perfis": [2, 3]  # Gestor E Fiscal (múltiplos perfis)
            },
            {
                "nome": "Fernanda Rocha",
                "email": "fernanda.rocha@pge.pa.gov.br",
                "cpf": "56789012345",
                "perfis": [3]  # Fiscal
            },
            {
                "nome": "Roberto Almeida",
                "email": "roberto.almeida@pge.pa.gov.br",
                "cpf": "67890123456",
                "perfis": [2]  # Gestor
            }
        ]

        senha_padrao = "senha123"
        hashed_password = bcrypt.hashpw(senha_padrao.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user_ids = {}
        for usuario in usuarios_exemplo:
            # Insere usuário (sem perfil_id - sistema de múltiplos perfis)
            user_id = await conn.fetchval(f"""
                INSERT INTO {users_table} (nome, email, cpf, senha_hash, ativo)
                VALUES ($1, $2, $3, $4, true)
                RETURNING id
            """, usuario["nome"], usuario["email"], usuario["cpf"], hashed_password)

            user_ids[usuario["email"]] = user_id

            # Concede perfis via usuario_perfil
            for perfil_id in usuario["perfis"]:
                await conn.execute("""
                    INSERT INTO usuario_perfil (usuario_id, perfil_id, ativo, data_concessao)
                    VALUES ($1, $2, true, NOW())
                """, user_id, perfil_id)

        # 2. CONTRATADOS DE EXEMPLO
        print("🏢 Criando contratados de exemplo...")

        contratados_exemplo = [
            {
                "nome": "Empresa de Limpeza LTDA",
                "cnpj": "12345678000195",
                "email": "contato@limpezaltda.com.br",
                "telefone": "(91) 3333-1111"
            },
            {
                "nome": "Construtora ABC S/A",
                "cnpj": "23456789000186",
                "email": "obras@construtorabc.com.br",
                "telefone": "(91) 3333-2222"
            },
            {
                "nome": "TI Solutions Tecnologia",
                "cnpj": "34567890000177",
                "email": "suporte@tisolutions.com.br",
                "telefone": "(91) 3333-3333"
            },
            {
                "nome": "Segurança Total EIRELI",
                "cnpj": "45678901000168",
                "email": "central@segurancatotal.com.br",
                "telefone": "(91) 3333-4444"
            },
            {
                "nome": "Transportes Rápidos LTDA",
                "cnpj": "56789012000159",
                "email": "logistica@transportesrapidos.com.br",
                "telefone": "(91) 3333-5555"
            }
        ]

        contractor_ids = {}
        for contratado in contratados_exemplo:
            contractor_id = await conn.fetchval(f"""
                INSERT INTO {contractors_table} (nome, cnpj, email, telefone, ativo)
                VALUES ($1, $2, $3, $4, true)
                RETURNING id
            """, contratado["nome"], contratado["cnpj"], contratado["email"], contratado["telefone"])

            contractor_ids[contratado["nome"]] = contractor_id

        # 3. CONTRATOS DE EXEMPLO
        print("📋 Criando contratos de exemplo...")

        # Busca IDs de usuários para gestores e fiscais
        admin_id = await conn.fetchval(f"SELECT id FROM {users_table} WHERE email = 'admin@sigescon.pge.pa.gov.br'")
        maria_id = user_ids["maria.silva@pge.pa.gov.br"]
        joao_id = user_ids["joao.oliveira@pge.pa.gov.br"]
        ana_id = user_ids["ana.costa@pge.pa.gov.br"]
        carlos_id = user_ids["carlos.lima@pge.pa.gov.br"]
        fernanda_id = user_ids["fernanda.rocha@pge.pa.gov.br"]
        roberto_id = user_ids["roberto.almeida@pge.pa.gov.br"]

        contratos_exemplo = [
            {
                "nr_contrato": "2024/001-PGE",
                "objeto": "Prestação de serviços de limpeza e conservação predial",
                "valor_anual": 120000.00,
                "valor_global": 360000.00,
                "data_inicio": date(2024, 1, 1),
                "data_fim": date(2026, 12, 31),
                "contratado": "Empresa de Limpeza LTDA",
                "modalidade_id": 1,  # Pregão Eletrônico
                "gestor_id": maria_id,
                "fiscal_id": joao_id,
                "fiscal_substituto_id": ana_id,
                "status_id": 1,  # Ativo
                "situacao": "pendencia_vencida"  # Para criar pendência vencida
            },
            {
                "nr_contrato": "2024/002-PGE",
                "objeto": "Obras de reforma e adequação do prédio administrativo",
                "valor_anual": 250000.00,
                "valor_global": 500000.00,
                "data_inicio": date(2024, 3, 1),
                "data_fim": date(2025, 2, 28),
                "contratado": "Construtora ABC S/A",
                "modalidade_id": 2,  # Concorrência
                "gestor_id": roberto_id,
                "fiscal_id": carlos_id,
                "status_id": 1,  # Ativo
                "situacao": "pendencia_analise"  # Para criar pendência em análise
            },
            {
                "nr_contrato": "2024/003-PGE",
                "objeto": "Suporte técnico e manutenção de sistemas de informação",
                "valor_anual": 80000.00,
                "valor_global": 160000.00,
                "data_inicio": date(2024, 6, 1),
                "data_fim": date(2025, 5, 31),
                "contratado": "TI Solutions Tecnologia",
                "modalidade_id": 3,  # Tomada de Preços
                "gestor_id": carlos_id,
                "fiscal_id": ana_id,
                "status_id": 1,  # Ativo
                "situacao": "relatorio_concluido"  # Para criar relatório aprovado
            },
            {
                "nr_contrato": "2024/004-PGE",
                "objeto": "Serviços de vigilância patrimonial armada",
                "valor_anual": 180000.00,
                "valor_global": 540000.00,
                "data_inicio": date(2024, 4, 1),
                "data_fim": date(2027, 3, 31),
                "contratado": "Segurança Total EIRELI",
                "modalidade_id": 1,  # Pregão Eletrônico
                "gestor_id": maria_id,
                "fiscal_id": fernanda_id,
                "fiscal_substituto_id": joao_id,
                "status_id": 1,  # Ativo
                "situacao": "relatorio_pendente"  # Para criar relatório aguardando análise
            },
            {
                "nr_contrato": "2024/005-PGE",
                "objeto": "Locação de veículos para transporte institucional",
                "valor_anual": 60000.00,
                "valor_global": 120000.00,
                "data_inicio": date(2024, 8, 1),
                "data_fim": date(2025, 7, 31),
                "contratado": "Transportes Rápidos LTDA",
                "modalidade_id": 5,  # Dispensa
                "gestor_id": roberto_id,
                "fiscal_id": joao_id,
                "status_id": 2,  # Suspenso
                "situacao": "normal"  # Contrato normal sem pendências
            }
        ]

        contract_ids = {}
        for contrato in contratos_exemplo:
            # Insere contrato
            contract_id = await conn.fetchval(f"""
                INSERT INTO {contracts_table} (
                    nr_contrato, objeto, valor_anual, valor_global, data_inicio, data_fim,
                    contratado_id, modalidade_id, status_id, gestor_id, fiscal_id, fiscal_substituto_id,
                    ativo
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, true)
                RETURNING id
            """,
                contrato["nr_contrato"], contrato["objeto"], contrato["valor_anual"], contrato["valor_global"],
                contrato["data_inicio"], contrato["data_fim"], contractor_ids[contrato["contratado"]],
                contrato["modalidade_id"], contrato["status_id"], contrato["gestor_id"],
                contrato["fiscal_id"], contrato.get("fiscal_substituto_id"),
            )

            contract_ids[contrato["nr_contrato"]] = {
                "id": contract_id,
                "situacao": contrato["situacao"],
                "fiscal_id": contrato["fiscal_id"]
            }

        # 4. CRIANDO SITUAÇÕES ESPECÍFICAS
        await create_specific_situations(conn, schema_type, contract_ids)

        print_success("Dados de exemplo inseridos com sucesso!")
        print_info("📊 Dados criados:")
        print_info(f"   • {len(usuarios_exemplo)} usuários de exemplo")
        print_info(f"   • {len(contratados_exemplo)} contratados")
        print_info(f"   • {len(contratos_exemplo)} contratos")
        print_info("   • Pendências vencidas, em análise e concluídas")
        print_info("   • Relatórios em diversos status")
        print_info("   • Arquivos de exemplo")

        return True

    except Exception as e:
        print_error(f"Erro ao inserir dados de exemplo: {e}")
        import traceback
        traceback.print_exc()
        return False

async def create_specific_situations(conn, schema_type, contract_ids):
    """Cria situações específicas solicitadas"""
    print("🎭 Criando situações específicas...")

    # Define nomes de tabelas baseado no schema
    if schema_type == "local":
        pendencias_table = "pendencias"
        relatorios_table = "relatorios"
        arquivos_table = "arquivos"
        status_pendencia_table = "status_pendencia"
        status_relatorio_table = "status_relatorio"
    else:
        pendencias_table = "pendenciarelatorio"
        relatorios_table = "relatoriofiscal"
        arquivos_table = "arquivo"
        status_pendencia_table = "statuspendencia"
        status_relatorio_table = "statusrelatorio"

    for nr_contrato, info in contract_ids.items():
        contract_id = info["id"]
        situacao = info["situacao"]
        fiscal_id = info["fiscal_id"]

        if situacao == "pendencia_vencida":
            # Cria pendência vencida (prazo expirado há 10 dias)
            if schema_type == "local":
                await conn.execute(f"""
                    INSERT INTO {pendencias_table} (
                        contrato_id, titulo, descricao, prazo_entrega, status_pendencia_id,
                        criado_por_usuario_id, data_criacao
                    ) VALUES ($1, $2, $3, $4, 1, $5, $6)
                """,
                    contract_id, "Relatório Mensal de Outubro",
                    "Enviar relatório mensal das atividades executadas no período de outubro/2024",
                    date.today() - timedelta(days=10), fiscal_id, datetime.now() - timedelta(days=20)
                )
            else:  # server - estrutura diferente
                await conn.execute(f"""
                    INSERT INTO {pendencias_table} (
                        contrato_id, descricao, data_prazo, status_pendencia_id,
                        criado_por_usuario_id
                    ) VALUES ($1, $2, $3, 1, $4)
                """,
                    contract_id,
                    "Relatório Mensal de Outubro - Enviar relatório mensal das atividades executadas no período de outubro/2024",
                    date.today() - timedelta(days=10),
                    fiscal_id
                )

        elif situacao == "pendencia_analise":
            # Cria pendência + relatório aguardando análise
            if schema_type == "local":
                pendencia_id = await conn.fetchval(f"""
                    INSERT INTO {pendencias_table} (
                        contrato_id, titulo, descricao, prazo_entrega, status_pendencia_id,
                        criado_por_usuario_id, data_criacao
                    ) VALUES ($1, $2, $3, $4, 1, $5, $6)
                    RETURNING id
                """,
                    contract_id, "Relatório Mensal de Novembro",
                    "Enviar relatório mensal das atividades executadas no período de novembro/2024",
                    date.today() + timedelta(days=5), fiscal_id, datetime.now() - timedelta(days=5)
                )
            else:  # server
                pendencia_id = await conn.fetchval(f"""
                    INSERT INTO {pendencias_table} (
                        contrato_id, descricao, data_prazo, status_pendencia_id,
                        criado_por_usuario_id
                    ) VALUES ($1, $2, $3, 1, $4)
                    RETURNING id
                """,
                    contract_id,
                    "Relatório Mensal de Novembro - Enviar relatório mensal das atividades executadas no período de novembro/2024",
                    date.today() + timedelta(days=5),
                    fiscal_id
                )

            # Cria relatório pendente de análise
            if schema_type == "local":
                await conn.execute(f"""
                    INSERT INTO {relatorios_table} (
                        contrato_id, fiscal_usuario_id, mes_competencia, status_relatorio_id,
                        observacoes_fiscal, pendencia_id, data_submissao
                    ) VALUES ($1, $2, $3, 1, $4, $5, $6)
                """,
                    contract_id, fiscal_id, date(2024, 11, 1),
                    "Relatório das atividades realizadas no mês de novembro conforme cronograma.",
                    pendencia_id, datetime.now() - timedelta(days=2)
                )
            else:  # server
                await conn.execute(f"""
                    INSERT INTO {relatorios_table} (
                        contrato_id, fiscal_usuario_id, mes_competencia, status_id,
                        observacoes_fiscal, pendencia_id, created_at
                    ) VALUES ($1, $2, $3, 1, $4, $5, $6)
                """,
                    contract_id, fiscal_id, date(2024, 11, 1),
                    "Relatório das atividades realizadas no mês de novembro conforme cronograma.",
                    pendencia_id, datetime.now() - timedelta(days=2)
                )

        elif situacao == "relatorio_concluido":
            # Cria pendência concluída + relatório aprovado
            if schema_type == "local":
                pendencia_id = await conn.fetchval(f"""
                    INSERT INTO {pendencias_table} (
                        contrato_id, titulo, descricao, prazo_entrega, status_pendencia_id,
                        criado_por_usuario_id, data_criacao
                    ) VALUES ($1, $2, $3, $4, 2, $5, $6)
                    RETURNING id
                """,
                    contract_id, "Relatório Mensal de Setembro",
                    "Enviar relatório mensal das atividades executadas no período de setembro/2024",
                    date(2024, 10, 5), fiscal_id, datetime.now() - timedelta(days=30)
                )
            else:  # server
                pendencia_id = await conn.fetchval(f"""
                    INSERT INTO {pendencias_table} (
                        contrato_id, descricao, data_prazo, status_pendencia_id,
                        criado_por_usuario_id
                    ) VALUES ($1, $2, $3, 2, $4)
                    RETURNING id
                """,
                    contract_id,
                    "Relatório Mensal de Setembro - Enviar relatório mensal das atividades executadas no período de setembro/2024",
                    date(2024, 10, 5),
                    fiscal_id
                )

            # Busca admin para ser o aprovador
            users_table_for_admin = "usuarios" if schema_type == "local" else "usuario"
            admin_id = await conn.fetchval(f"SELECT id FROM {users_table_for_admin} WHERE email = 'admin@sigescon.pge.pa.gov.br'")

            # Cria relatório aprovado (adapta campos conforme schema)
            if schema_type == "local":
                await conn.execute(f"""
                    INSERT INTO {relatorios_table} (
                        contrato_id, fiscal_usuario_id, mes_competencia, status_relatorio_id,
                        observacoes_fiscal, aprovador_usuario_id, data_analise,
                        observacoes_aprovador, pendencia_id, data_submissao
                    ) VALUES ($1, $2, $3, 2, $4, $5, $6, $7, $8, $9)
                """,
                    contract_id, fiscal_id, date(2024, 9, 1),
                    "Relatório das atividades realizadas conforme planejado.",
                    admin_id, datetime.now() - timedelta(days=15),
                    "Relatório aprovado. Atividades executadas dentro do cronograma.",
                    pendencia_id, datetime.now() - timedelta(days=20)
                )
            else:  # server
                await conn.execute(f"""
                    INSERT INTO {relatorios_table} (
                        contrato_id, fiscal_usuario_id, mes_competencia, status_id,
                        observacoes_fiscal, aprovador_usuario_id, data_analise,
                        observacoes_aprovador, pendencia_id, created_at
                    ) VALUES ($1, $2, $3, 2, $4, $5, $6, $7, $8, $9)
                """,
                    contract_id, fiscal_id, date(2024, 9, 1),
                    "Relatório das atividades realizadas conforme planejado.",
                    admin_id, datetime.now() - timedelta(days=15),
                    "Relatório aprovado. Atividades executadas dentro do cronograma.",
                    pendencia_id, datetime.now() - timedelta(days=20)
                )

        elif situacao == "relatorio_pendente":
            # Cria pendência + relatório pendente de análise
            if schema_type == "local":
                pendencia_id = await conn.fetchval(f"""
                    INSERT INTO {pendencias_table} (
                        contrato_id, titulo, descricao, prazo_entrega, status_pendencia_id,
                        criado_por_usuario_id, data_criacao
                    ) VALUES ($1, $2, $3, $4, 1, $5, $6)
                    RETURNING id
                """,
                    contract_id, "Relatório Trimestral - Q4/2024",
                    "Enviar relatório trimestral das atividades do quarto trimestre de 2024",
                    date.today() + timedelta(days=15), fiscal_id, datetime.now() - timedelta(days=10)
                )
            else:  # server
                pendencia_id = await conn.fetchval(f"""
                    INSERT INTO {pendencias_table} (
                        contrato_id, descricao, data_prazo, status_pendencia_id,
                        criado_por_usuario_id
                    ) VALUES ($1, $2, $3, 1, $4)
                    RETURNING id
                """,
                    contract_id,
                    "Relatório Trimestral Q4/2024 - Enviar relatório trimestral das atividades do quarto trimestre de 2024",
                    date.today() + timedelta(days=15),
                    fiscal_id
                )

            # Cria relatório aguardando análise
            if schema_type == "local":
                await conn.execute(f"""
                    INSERT INTO {relatorios_table} (
                        contrato_id, fiscal_usuario_id, mes_competencia, status_relatorio_id,
                        observacoes_fiscal, pendencia_id, data_submissao
                    ) VALUES ($1, $2, $3, 1, $4, $5, $6)
                """,
                    contract_id, fiscal_id, date(2024, 12, 1),
                    "Relatório trimestral com resumo executivo das atividades do período.",
                    pendencia_id, datetime.now() - timedelta(hours=6)
                )
            else:  # server
                await conn.execute(f"""
                    INSERT INTO {relatorios_table} (
                        contrato_id, fiscal_usuario_id, mes_competencia, status_id,
                        observacoes_fiscal, pendencia_id, created_at
                    ) VALUES ($1, $2, $3, 1, $4, $5, $6)
                """,
                    contract_id, fiscal_id, date(2024, 12, 1),
                    "Relatório trimestral com resumo executivo das atividades do período.",
                    pendencia_id, datetime.now() - timedelta(hours=6)
                )

    # Cria alguns arquivos de exemplo (simulados)
    print("📎 Criando arquivos de exemplo...")

    primeiro_contrato_id = list(contract_ids.values())[0]["id"]

    # Simula arquivos PDF do contrato
    arquivos_exemplo = [
        {
            "nome": "contrato_principal.pdf",
            "tipo": "application/pdf",
            "tamanho": 1987456
        },
        {
            "nome": "termo_aditivo_01.pdf",
            "tipo": "application/pdf",
            "tamanho": 856234
        },
        {
            "nome": "cronograma_execucao.xlsx",
            "tipo": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "tamanho": 245678
        }
    ]

    for arquivo in arquivos_exemplo:
        await conn.execute(f"""
            INSERT INTO {arquivos_table} (
                nome_arquivo, tipo_arquivo, tamanho_bytes, contrato_id, path_armazenamento
            ) VALUES ($1, $2, $3, $4, $5)
        """,
            arquivo["nome"],
            arquivo["tipo"],
            arquivo["tamanho"],
            primeiro_contrato_id,
            f"/uploads/contratos/{primeiro_contrato_id}/{arquivo['nome']}"
        )

    print_success("Situações específicas criadas com sucesso!")
    print_info("✨ Criado:")
    print_info("   • Contrato com pendência vencida há 10 dias")
    print_info("   • Contrato com relatório aguardando análise")
    print_info("   • Contrato com relatório aprovado e pendência concluída")
    print_info("   • Contrato com relatório trimestral pendente")
    print_info("   • Contrato suspenso sem movimentação")
    print_info("   • 3 arquivos PDF/Excel de exemplo")