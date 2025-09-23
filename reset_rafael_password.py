#!/usr/bin/env python3
"""
Script para resetar a senha do usuário Rafael
"""
import asyncio
import asyncpg
from passlib.context import CryptContext

async def reset_password():
    """Reset Rafael's password"""

    print("🔐 Resetando senha do usuário Rafael...")

    # Database connection
    DATABASE_URL = "postgresql://root:xpto1661WIN@10.96.0.67:5432/contratos"

    # Password hashing
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    new_password = "xpto1661WIN"
    hashed_password = pwd_context.hash(new_password)

    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)

        # Update Rafael's password
        result = await conn.execute(
            "UPDATE usuario SET senha_hash = $1 WHERE email = $2",
            hashed_password,
            "rafael.costa@pge.pa.gov.br"
        )

        print(f"✅ Senha atualizada para Rafael. Resultado: {result}")

        # Verify the update
        user = await conn.fetchrow(
            "SELECT id, nome, email FROM usuario WHERE email = $1",
            "rafael.costa@pge.pa.gov.br"
        )

        if user:
            print(f"✅ Usuário verificado: {user['nome']} (ID: {user['id']})")
        else:
            print("❌ Usuário não encontrado após atualização")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Erro ao resetar senha: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(reset_password())
    if success:
        print("🎉 Senha resetada com sucesso! Agora Rafael pode fazer login.")
    else:
        print("💥 Falha ao resetar senha.")