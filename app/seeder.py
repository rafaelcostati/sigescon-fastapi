# app/seeder.py
import asyncpg
from app.core.config import settings
from app.core.security import get_password_hash

async def seed_data(conn: asyncpg.Connection):
    """Popula o banco com dados essenciais para o teste."""
    print("Iniciando o processo de seed do banco de dados de teste...")

    # --- Inserir Perfis ---
    perfis = ['Administrador', 'Gestor', 'Fiscal']
    for perfil_nome in perfis:
        exists = await conn.fetchval("SELECT 1 FROM perfil WHERE nome = $1", perfil_nome)
        if not exists:
            await conn.execute("INSERT INTO perfil (nome) VALUES ($1)", perfil_nome)
            print(f"- Perfil '{perfil_nome}' criado.")

    # --- Inserir Usuário Administrador ---
    admin_email = settings.ADMIN_EMAIL
    if admin_email:
        exists = await conn.fetchval("SELECT 1 FROM usuario WHERE email = $1", admin_email)
        if not exists:
            admin_pass_hash = get_password_hash(settings.ADMIN_PASSWORD)
            perfil_admin_id = await conn.fetchval("SELECT id FROM perfil WHERE nome = 'Administrador'")
            
            await conn.execute(
                """
                INSERT INTO usuario (nome, email, cpf, senha, perfil_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                'Admin de Teste', admin_email, '00000000000', admin_pass_hash, perfil_admin_id
            )
            print(f"- Usuário Administrador '{admin_email}' criado.")
    
    print("Seed do banco de dados de teste concluído.")