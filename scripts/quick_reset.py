#!/usr/bin/env python3
"""
Script rápido para resetar banco - sem confirmação interativa
Para uso em desenvolvimento/CI

Uso:
    python scripts/quick_reset.py
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.reset_and_seed_database import reset_and_seed_database

async def main():
    print("🚀 Executando reset rápido do banco...")
    await reset_and_seed_database()

if __name__ == "__main__":
    asyncio.run(main())