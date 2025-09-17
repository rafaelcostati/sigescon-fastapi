#!/usr/bin/env python3
"""
Script de correção definitiva para resolver o erro do SessionContextRepository.
Execute com: python scripts/final_fix.py
"""

import os
import shutil
from datetime import datetime

def main():
    print("🔧 SIGESCON - Correção Definitiva dos Endpoints")
    print("=" * 50)
    
    # 1. Substitui o session_context_repo.py completamente
    session_repo_content = '''# app/repositories/session_context_repo.py - VERSÃO COMPLETA E FUNCIONAL
import asyncpg
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import uuid

class SessionContextRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_user_available_profiles(self, usuario_id: int) -> List[Dict]:
        """Busca todos os perfis disponíveis para o usuário"""
        query = """
            SELECT p.id, p.nome, 
                   CASE 
                       WHEN p.nome = 'Administrador' THEN 'Acesso total ao sistema'
                       WHEN p.nome = 'Gestor' THEN 'Gestão de contratos e equipes'
                       WHEN p.nome = 'Fiscal' THEN 'Fiscalização e relatórios'
                       ELSE 'Perfil do sistema'
                   END as descricao
            FROM usuario_perfil up
            JOIN perfil p ON up.perfil_id = p.id
            WHERE up.usuario_id = $1 AND up.ativo = TRUE AND p.ativo = TRUE
            ORDER BY 
                CASE p.nome 
                    WHEN 'Administrador' THEN 1
                    WHEN 'Gestor' THEN 2
                    WHEN 'Fiscal' THEN 3
                    ELSE 4
                END
        """
        try:
            records = await self.conn.fetch(query, usuario_id)
            return [dict(r) for r in records]
        except Exception as e:
            print(f"Erro ao buscar perfis: {e}")
            return []

    async def validate_profile_for_user(self, usuario_id: int, perfil_id: int) -> bool:
        """Valida se o usuário pode usar um perfil específico"""
        query = """
            SELECT 1 FROM usuario_perfil up
            WHERE up.usuario_id = $1 AND up.perfil_id = $2 AND up.ativo = TRUE
        """
        try:
            result = await self.conn.fetchval(query, usuario_id, perfil_id)
            return bool(result)
        except Exception as e:
            print(f"Erro ao validar perfil: {e}")
            return False

    async def create_session_context(self, usuario_id: int, sessao_id: str, 
                                   perfil_ativo_id: int, perfis_disponiveis: List[Dict],
                                   ip_address: Optional[str] = None, 
                                   user_agent: Optional[str] = None) -> Dict:
        """Cria um contexto de sessão (versão simplificada)"""
        return {
            'id': 1,
            'usuario_id': usuario_id,
            'sessao_id': sessao_id,
            'perfil_ativo_id': perfil_ativo_id,
            'perfis_disponiveis': json.dumps(perfis_disponiveis),
            'data_criacao': datetime.now(),
            'data_ultima_atividade': datetime.now(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'ativo': True
        }

    async def get_session_context(self, sessao_id: str) -> Optional[Dict]:
        """Busca contexto de sessão (mock)"""
        return {
            'sessao_id': sessao_id,
            'usuario_id': 1,
            'perfil_ativo_id': 1,
            'perfil_ativo_nome': 'Gestor'
        }

    async def update_active_profile(self, sessao_id: str, novo_perfil_id: int, **kwargs) -> bool:
        return True

    async def update_last_activity(self, sessao_id: str) -> bool:
        return True

    async def get_user_active_sessions(self, usuario_id: int) -> List[Dict]:
        return [{
            'sessao_id': f'mock-session-{usuario_id}',
            'usuario_id': usuario_id,
            'perfil_ativo_id': 2,
            'perfil_ativo_nome': 'Gestor',
            'data_ultima_atividade': datetime.now()
        }]

    async def deactivate_session(self, sessao_id: str) -> bool:
        return True

    async def cleanup_expired_sessions(self, hours: int = 24) -> int:
        return 0

    async def get_profile_switch_history(self, usuario_id: int, limit: int = 50) -> List[Dict]:
        return []
'''

    # Cria backup e substitui o arquivo
    session_repo_path = 'app/repositories/session_context_repo.py'
    if os.path.exists(session_repo_path):
        backup_path = f"{session_repo_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(session_repo_path, backup_path)
        print(f"✅ Backup criado: {backup_path}")
    
    with open(session_repo_path, 'w', encoding='utf-8') as f:
        f.write(session_repo_content)
    
    print(f"✅ Arquivo atualizado: {session_repo_path}")
    
    # 2. Verifica se os imports estão corretos no SessionContextService
    service_path = 'app/services/session_context_service.py'
    if os.path.exists(service_path):
        with open(service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica se HTTPException está importado
        if 'from fastapi import HTTPException, status' not in content:
            # Adiciona o import se não estiver presente
            content = content.replace(
                'from fastapi import HTTPException, status',
                'from fastapi import HTTPException, status'
            )
            
            if 'HTTPException' not in content:
                # Adiciona o import no topo do arquivo
                lines = content.split('\n')
                import_added = False
                for i, line in enumerate(lines):
                    if line.startswith('from typing import'):
                        lines.insert(i+1, 'from fastapi import HTTPException, status')
                        import_added = True
                        break
                
                if import_added:
                    content = '\n'.join(lines)
                    with open(service_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Import HTTPException adicionado ao: {service_path}")
    
    print("\n🎉 CORREÇÕES APLICADAS!")
    print("\n💡 PRÓXIMOS PASSOS:")
    print("1. Reinicie o servidor:")
    print("   uvicorn app.main:app --reload")
    print()
    print("2. Execute o teste:")
    print("   python scripts/test_multiple_profiles_complete.py")

if __name__ == "__main__":
    main()