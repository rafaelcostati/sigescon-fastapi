# app/services/pendencia_service.py
from typing import List
from fastapi import HTTPException, status

# Repositórios
from app.repositories.pendencia_repo import PendenciaRepository
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.status_pendencia_repo import StatusPendenciaRepository

# Schemas
from app.schemas.pendencia_schema import Pendencia, PendenciaCreate

# Services
from app.services.email_service import EmailService

class PendenciaService:
    def __init__(self,
                 pendencia_repo: PendenciaRepository,
                 contrato_repo: ContratoRepository,
                 usuario_repo: UsuarioRepository,
                 status_pendencia_repo: StatusPendenciaRepository):
        self.pendencia_repo = pendencia_repo
        self.contrato_repo = contrato_repo
        self.usuario_repo = usuario_repo
        self.status_pendencia_repo = status_pendencia_repo

    async def _validate_foreign_keys(self, pendencia: PendenciaCreate, contrato_id: int):
        """Valida se todas as chaves estrangeiras existem"""
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
        
        if not await self.usuario_repo.get_user_by_id(pendencia.criado_por_usuario_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário criador não encontrado")

        if not await self.status_pendencia_repo.get_by_id(pendencia.status_pendencia_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de pendência não encontrado")

    async def create_pendencia(self, contrato_id: int, pendencia_create: PendenciaCreate) -> Pendencia:
        """Cria uma nova pendência e envia notificação por email para o fiscal"""
        await self._validate_foreign_keys(pendencia_create, contrato_id)
        
        # Cria a pendência no banco de dados
        new_pendencia_data = await self.pendencia_repo.create_pendencia(contrato_id, pendencia_create)
        
        # === NOTIFICAÇÃO POR EMAIL COM TEMPLATES ===
        try:
            contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
            if contrato and contrato.get('fiscal_id'):
                fiscal = await self.usuario_repo.get_user_by_id(contrato['fiscal_id'])
                if fiscal:
                    from app.services.email_templates import EmailTemplates
                    
                    subject, body = EmailTemplates.pending_report_notification(
                        fiscal_nome=fiscal['nome'],
                        contrato_data=contrato,
                        pendencia_data=new_pendencia_data
                    )
                    await EmailService.send_email(fiscal['email'], subject, body)
                    
                    print(f"✅ Email de pendência enviado para {fiscal['email']}")
        except Exception as e:
            # Log do erro, mas não falha a criação da pendência
            print(f"❌ Erro ao enviar email de notificação da pendência {new_pendencia_data['id']}: {e}")
        
        return Pendencia.model_validate(new_pendencia_data)

    async def get_pendencias_by_contrato_id(self, contrato_id: int) -> List[Pendencia]:
        """Lista todas as pendências de um contrato específico"""
        if not await self.contrato_repo.find_contrato_by_id(contrato_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
            
        pendencias_data = await self.pendencia_repo.get_pendencias_by_contrato_id(contrato_id)
        return [Pendencia.model_validate(p) for p in pendencias_data]

    async def get_pendencia_by_id(self, pendencia_id: int) -> Pendencia:
        """Busca uma pendência específica pelo ID"""
        pendencia_data = await self.pendencia_repo.get_pendencia_by_id(pendencia_id)
        if not pendencia_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pendência não encontrada")
        
        return Pendencia.model_validate(pendencia_data)

    async def update_pendencia_status(self, pendencia_id: int, novo_status_id: int) -> Pendencia:
        """Atualiza o status de uma pendência"""
        # Verifica se a pendência existe
        if not await self.pendencia_repo.get_pendencia_by_id(pendencia_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pendência não encontrada")
        
        # Verifica se o status existe
        if not await self.status_pendencia_repo.get_by_id(novo_status_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de pendência não encontrado")
        
        # Atualiza o status
        await self.pendencia_repo.update_pendencia_status(pendencia_id, novo_status_id)
        
        # Retorna a pendência atualizada
        return await self.get_pendencia_by_id(pendencia_id)

    async def get_pendencias_vencendo(self, dias_antecedencia: int = 7) -> List[Pendencia]:
        """Busca pendências que estão vencendo nos próximos X dias"""
        from datetime import date, timedelta
        
        data_limite = date.today() + timedelta(days=dias_antecedencia)
        
        # Busca pendências que vencem até a data limite
        pendencias_due = await self.pendencia_repo.get_due_pendencias()
        
        pendencias_vencendo = []
        for pendencia_data in pendencias_due:
            if pendencia_data['data_prazo'] <= data_limite:
                pendencias_vencendo.append(Pendencia.model_validate(pendencia_data))
        
        return pendencias_vencendo

    async def send_deadline_reminders(self) -> int:
        """
        Envia lembretes de prazo para pendências que estão vencendo.
        Retorna o número de emails enviados.
        """
        from datetime import date
        
        emails_enviados = 0
        
        try:
            # Busca todas as pendências com status 'Pendente'
            pendencias_due = await self.pendencia_repo.get_due_pendencias()
            
            today = date.today()
            
            for pendencia_data in pendencias_due:
                prazo = pendencia_data['data_prazo']
                if isinstance(prazo, str):
                    from datetime import datetime
                    prazo = datetime.strptime(prazo, '%Y-%m-%d').date()
                
                dias_restantes = (prazo - today).days
                
                # Envia lembrete em intervalos específicos: 15, 7, 3, 1, 0 dias
                if dias_restantes in [15, 7, 3, 1, 0]:
                    try:
                        # Busca dados completos do contrato para o template
                        contrato = await self.contrato_repo.find_contrato_by_id(pendencia_data['contrato_id'])
                        
                        if contrato:
                            from app.services.email_templates import EmailTemplates
                            
                            subject, body = EmailTemplates.pending_report_notification(
                                fiscal_nome=pendencia_data['fiscal_nome'],
                                contrato_data=contrato,
                                pendencia_data=pendencia_data
                            )
                            
                            await EmailService.send_email(pendencia_data['fiscal_email'], subject, body)
                            emails_enviados += 1
                            
                            print(f"✅ Lembrete enviado para {pendencia_data['fiscal_nome']} - {dias_restantes} dias restantes")
                    
                    except Exception as e:
                        print(f"❌ Erro ao enviar lembrete para pendência {pendencia_data['id']}: {e}")
            
            print(f"📧 Total de lembretes enviados: {emails_enviados}")
            return emails_enviados
            
        except Exception as e:
            print(f"❌ Erro geral ao enviar lembretes de prazo: {e}")
            return 0

    async def get_pendencias_by_fiscal(self, fiscal_id: int) -> List[Pendencia]:
        """Busca todas as pendências atribuídas a um fiscal específico"""
        # Verifica se o fiscal existe
        if not await self.usuario_repo.get_user_by_id(fiscal_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal não encontrado")
        
        # Busca contratos onde o usuário é fiscal
        contratos_data, _ = await self.contrato_repo.get_all_contratos(
            filters={'fiscal_id': fiscal_id},
            limit=1000,  # Limite alto para pegar todos
            offset=0
        )
        
        pendencias_fiscal = []
        for contrato in contratos_data:
            pendencias_contrato = await self.get_pendencias_by_contrato_id(contrato['id'])
            pendencias_fiscal.extend(pendencias_contrato)
        
        return pendencias_fiscal

    async def cancel_pendencia(self, pendencia_id: int, usuario_id: int) -> Pendencia:
        """Cancela uma pendência (muda status para 'Cancelada')"""
        # Busca o status 'Cancelada'
        all_status = await self.status_pendencia_repo.get_all()
        status_cancelada = next((s for s in all_status if s['nome'] == 'Cancelada'), None)
        
        if not status_cancelada:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Status 'Cancelada' não encontrado no sistema"
            )
        
        # Atualiza o status da pendência
        return await self.update_pendencia_status(pendencia_id, status_cancelada['id'])