# app/services/usuario_perfil_service.py
from typing import List, Optional
from fastapi import HTTPException, status

from app.repositories.usuario_perfil_repo import UsuarioPerfilRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.perfil_repo import PerfilRepository
from app.schemas.usuario_perfil_schema import (
    UsuarioPerfil, UsuarioComPerfis, PerfilWithUsers, 
    HistoricoPerfilConcessao, ValidacaoPerfil,
    UsuarioPerfilGrantRequest, UsuarioPerfilRevokeRequest
)

class UsuarioPerfilService:
    def __init__(self, 
                 usuario_perfil_repo: UsuarioPerfilRepository,
                 usuario_repo: UsuarioRepository,
                 perfil_repo: PerfilRepository):
        self.usuario_perfil_repo = usuario_perfil_repo
        self.usuario_repo = usuario_repo
        self.perfil_repo = perfil_repo

    async def get_user_profiles(self, usuario_id: int) -> List[UsuarioPerfil]:
        """Busca todos os perfis de um usuário"""
        # Verifica se o usuário existe
        if not await self.usuario_repo.get_user_by_id(usuario_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        perfis_data = await self.usuario_perfil_repo.get_user_profiles(usuario_id)
        return [UsuarioPerfil.model_validate(p) for p in perfis_data]

    async def get_user_complete_info(self, usuario_id: int) -> UsuarioComPerfis:
        """Busca informações completas do usuário incluindo perfis"""
        user_data = await self.usuario_perfil_repo.get_user_complete_info(usuario_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Converte arrays PostgreSQL para listas Python
        if user_data.get('perfis'):
            user_data['perfis_texto'] = ', '.join(user_data['perfis'])
        else:
            user_data['perfis'] = []
            user_data['perfil_ids'] = []
            user_data['perfis_texto'] = ""
        
        return UsuarioComPerfis.model_validate(user_data)

    async def grant_profiles_to_user(self, usuario_id: int, request: UsuarioPerfilGrantRequest, 
                                   admin_id: int) -> List[UsuarioPerfil]:
        """Concede múltiplos perfis a um usuário"""
        # Validações
        if not await self.usuario_repo.get_user_by_id(usuario_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Valida se todos os perfis existem
        for perfil_id in request.perfil_ids:
            if not await self.perfil_repo.get_perfil_by_id(perfil_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Perfil com ID {perfil_id} não encontrado"
                )
        
        # Concede os perfis
        granted_profiles = []
        for perfil_id in request.perfil_ids:
            profile_result = await self.usuario_perfil_repo.add_profile_to_user(
                usuario_id=usuario_id,
                perfil_id=perfil_id,
                concedido_por=admin_id
            )
            
            # Busca dados completos do perfil concedido
            complete_profile = await self.usuario_perfil_repo.get_user_profiles(usuario_id)
            granted_profile = next((p for p in complete_profile if p['perfil_id'] == perfil_id), None)
            
            if granted_profile:
                granted_profiles.append(UsuarioPerfil.model_validate(granted_profile))
        
        return granted_profiles

    async def revoke_profiles_from_user(self, usuario_id: int, request: UsuarioPerfilRevokeRequest) -> bool:
        """Revoga múltiplos perfis de um usuário"""
        if not await self.usuario_repo.get_user_by_id(usuario_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Verifica se pelo menos um perfil será mantido
        current_profiles = await self.usuario_perfil_repo.get_user_profiles(usuario_id)
        remaining_profiles = [p for p in current_profiles if p['perfil_id'] not in request.perfil_ids]
        
        if not remaining_profiles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível revogar todos os perfis. O usuário deve manter pelo menos um perfil ativo."
            )
        
        # Revoga os perfis
        success_count = 0
        for perfil_id in request.perfil_ids:
            if await self.usuario_perfil_repo.remove_profile_from_user(usuario_id, perfil_id):
                success_count += 1
        
        return success_count > 0

    async def get_available_fiscals(self) -> List[UsuarioComPerfis]:
        """Lista usuários que podem exercer função de fiscal"""
        users_data = await self.usuario_perfil_repo.get_available_fiscals()
        
        complete_users = []
        for user_data in users_data:
            complete_info = await self.get_user_complete_info(user_data['id'])
            complete_users.append(complete_info)
        
        return complete_users

    async def get_available_managers(self) -> List[UsuarioComPerfis]:
        """Lista usuários que podem exercer função de gestor"""
        users_data = await self.usuario_perfil_repo.get_available_managers()
        
        complete_users = []
        for user_data in users_data:
            complete_info = await self.get_user_complete_info(user_data['id'])
            complete_users.append(complete_info)
        
        return complete_users

    async def validate_user_permissions(self, usuario_id: int) -> ValidacaoPerfil:
        """Valida as permissões de um usuário"""
        if not await self.usuario_repo.get_user_by_id(usuario_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Busca perfis do usuário
        perfis_data = await self.usuario_perfil_repo.get_user_profiles(usuario_id)
        perfis_nomes = [p['perfil_nome'] for p in perfis_data]
        
        # Validações específicas
        pode_ser_fiscal = await self.usuario_perfil_repo.validate_user_can_be_fiscal(usuario_id)
        pode_ser_gestor = await self.usuario_perfil_repo.validate_user_can_be_manager(usuario_id)
        pode_ser_admin = "Administrador" in perfis_nomes
        
        return ValidacaoPerfil(
            usuario_id=usuario_id,
            pode_ser_fiscal=pode_ser_fiscal,
            pode_ser_gestor=pode_ser_gestor,
            pode_ser_admin=pode_ser_admin,
            perfis_ativos=perfis_nomes
        )

    async def get_users_by_profile(self, perfil_name: str) -> PerfilWithUsers:
        """Lista todos os usuários que possuem um perfil específico"""
        # Verifica se o perfil existe
        all_perfis = await self.perfil_repo.get_all_perfis()
        perfil = next((p for p in all_perfis if p['nome'] == perfil_name), None)
        
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Perfil '{perfil_name}' não encontrado"
            )
        
        # Busca usuários com este perfil
        users_data = await self.usuario_perfil_repo.get_users_by_profile(perfil_name, include_details=True)
        
        return PerfilWithUsers(
            id=perfil['id'],
            nome=perfil['nome'],
            ativo=perfil['ativo'],
            usuarios=users_data,
            total_usuarios=len(users_data)
        )

    async def get_profile_history(self, usuario_id: int) -> List[HistoricoPerfilConcessao]:
        """Busca histórico de concessão/remoção de perfis de um usuário"""
        if not await self.usuario_repo.get_user_by_id(usuario_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        history_data = await self.usuario_perfil_repo.get_profile_grant_history(usuario_id)
        return [HistoricoPerfilConcessao.model_validate(h) for h in history_data]

    async def has_profile(self, usuario_id: int, perfil_name: str) -> bool:
        """Verifica se um usuário tem um perfil específico"""
        return await self.usuario_perfil_repo.has_profile(usuario_id, perfil_name)

    async def has_any_profile(self, usuario_id: int, perfil_names: List[str]) -> bool:
        """Verifica se um usuário tem pelo menos um dos perfis especificados"""
        return await self.usuario_perfil_repo.has_any_profile(usuario_id, perfil_names)

    async def migrate_single_profile_user(self, usuario_id: int, admin_id: int) -> UsuarioComPerfis:
        """Migra usuário do sistema antigo (perfil único) para o novo (perfis múltiplos)"""
        # Busca o usuário no sistema antigo
        user = await self.usuario_repo.get_user_by_id(usuario_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Verifica se já foi migrado
        existing_profiles = await self.usuario_perfil_repo.get_user_profiles(usuario_id)
        if existing_profiles:
            # Já migrado, retorna informações atuais
            return await self.get_user_complete_info(usuario_id)
        
        # Migra o perfil único para o sistema de perfis múltiplos
        if hasattr(user, 'perfil_id') and user.get('perfil_id'):
            await self.usuario_perfil_repo.add_profile_to_user(
                usuario_id=usuario_id,
                perfil_id=user['perfil_id'],
                concedido_por=admin_id
            )
        
        return await self.get_user_complete_info(usuario_id)

    async def bulk_grant_profile(self, usuario_ids: List[int], perfil_id: int, 
                                admin_id: int) -> dict:
        """Concede um perfil a múltiplos usuários"""
        # Verifica se o perfil existe
        if not await self.perfil_repo.get_perfil_by_id(perfil_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
        
        results = {
            "success": [],
            "failed": [],
            "already_granted": []
        }
        
        for usuario_id in usuario_ids:
            try:
                # Verifica se o usuário existe
                if not await self.usuario_repo.get_user_by_id(usuario_id):
                    results["failed"].append({
                        "usuario_id": usuario_id,
                        "reason": "Usuário não encontrado"
                    })
                    continue
                
                # Verifica se já possui o perfil
                if await self.usuario_perfil_repo.has_profile(usuario_id, ""):  # Precisa ajustar para usar ID
                    user_profiles = await self.usuario_perfil_repo.get_user_profiles(usuario_id)
                    if any(p['perfil_id'] == perfil_id for p in user_profiles):
                        results["already_granted"].append(usuario_id)
                        continue
                
                # Concede o perfil
                await self.usuario_perfil_repo.add_profile_to_user(
                    usuario_id=usuario_id,
                    perfil_id=perfil_id,
                    concedido_por=admin_id
                )
                results["success"].append(usuario_id)
                
            except Exception as e:
                results["failed"].append({
                    "usuario_id": usuario_id,
                    "reason": str(e)
                })
        
        return results