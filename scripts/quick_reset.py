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
    import argparse
    parser = argparse.ArgumentParser(description='Reset rápido do banco de dados SIGESCON')
    parser.add_argument('--clean', action='store_true',
                       help='Modo clean: cria apenas dados essenciais (perfis, status, admin)')
    args = parser.parse_args()

    mode_text = " (modo clean)" if args.clean else ""
    print(f"🚀 Executando reset rápido do banco{mode_text}...")
    await reset_and_seed_database(clean_mode=args.clean)

if __name__ == "__main__":
    asyncio.run(main())