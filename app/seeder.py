# app/seeder.py
import asyncpg
import re
from app.core.config import settings
from app.core.security import get_password_hash

async def seed_data(conn: asyncpg.Connection):
    """
    Popula o banco com dados essenciais para o teste,
    corrigindo o CPF do admin se estiver inconsistente.
    """
    print("Iniciando o processo de seed do banco de dados de teste...")

    # --- Inserir Perfis ---
    perfis = ['Administrador', 'Gestor', 'Fiscal']
    for perfil_nome in perfis:
        exists = await conn.fetchval("SELECT 1 FROM perfil WHERE nome = $1", perfil_nome)
        if not exists:
            await conn.execute("INSERT INTO perfil (nome) VALUES ($1)", perfil_nome)
            print(f"- Perfil '{perfil_nome}' criado.")

    # --- Garantir a integridade do Usuário Administrador ---
    admin_email = settings.ADMIN_EMAIL
    if admin_email:
        admin_user = await conn.fetchrow("SELECT id, cpf FROM usuario WHERE email = $1", admin_email)
        valid_cpf = "12345678901"  # CPF padrão válido para o admin de teste
        
        if not admin_user:
            # Se o usuário não existe, cria com o CPF correto
            print(f"Usuário admin '{admin_email}' não encontrado. Criando...")
            admin_pass_hash = get_password_hash(settings.ADMIN_PASSWORD)
            perfil_admin_id = await conn.fetchval("SELECT id FROM perfil WHERE nome = 'Administrador'")
            
            await conn.execute(
                """
                INSERT INTO usuario (nome, email, cpf, senha, perfil_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                'Admin de Teste', admin_email, valid_cpf, admin_pass_hash, perfil_admin_id
            )
            print(f"- Usuário Administrador '{admin_email}' criado com CPF válido.")
        else:
            # Se o usuário já existe, verifica se o CPF é válido
            current_cpf = admin_user['cpf']
            # Validação simples: verifica se o CPF contém 11 dígitos numéricos
            is_valid = current_cpf and len(re.sub(r'\D', '', current_cpf)) == 11
            
            if not is_valid:
                print(f"Usuário admin '{admin_email}' encontrado com CPF inválido ('{current_cpf}'). Corrigindo...")
                await conn.execute("UPDATE usuario SET cpf = $1 WHERE email = $2", valid_cpf, admin_email)
                print(f"- CPF do admin atualizado para '{valid_cpf}'.")
            else:
                print(f"Usuário admin '{admin_email}' já existe com CPF válido.")
    
    print("Seed do banco de dados de teste concluído.")