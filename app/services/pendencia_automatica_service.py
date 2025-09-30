# app/services/pendencia_automatica_service.py
import asyncio
from datetime import date, timedelta
from typing import List, Dict, Any
from fastapi import HTTPException, status
from app.repositories.contrato_repo import ContratoRepository
from app.repositories.config_repo import ConfigRepository
from app.repositories.status_pendencia_repo import StatusPendenciaRepository

class PendenciaAutomaticaService:
    """
    Serviço para calcular e gerar pendências automáticas para contratos
    """

    def __init__(
        self,
        contrato_repo: ContratoRepository,
        config_repo: ConfigRepository,
        status_pendencia_repo: StatusPendenciaRepository
    ):
        self.contrato_repo = contrato_repo
        self.config_repo = config_repo
        self.status_pendencia_repo = status_pendencia_repo

    async def calcular_pendencias_automaticas(self, contrato_id: int) -> Dict[str, Any]:
        """
        Calcula as pendências automáticas que serão criadas para um contrato
        baseado na data de início, fim e intervalo configurado.

        Retorna um preview das pendências que serão criadas para aprovação do admin.
        """
        # Busca o contrato
        contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
        if not contrato:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado"
            )

        # Verifica se o contrato tem data de início e fim
        data_inicio = contrato.get('data_inicio')
        data_fim = contrato.get('data_fim')

        if not data_inicio or not data_fim:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contrato deve ter data de início e fim definidas"
            )

        # Converte strings para date se necessário
        if isinstance(data_inicio, str):
            from datetime import datetime
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if isinstance(data_fim, str):
            from datetime import datetime
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

        # Busca o intervalo configurado
        intervalo_dias = await self.config_repo.get_pendencias_intervalo_dias()

        # Calcula as datas das pendências
        pendencias_preview = []
        data_atual = data_inicio + timedelta(days=intervalo_dias)
        contador = 1

        while data_atual <= data_fim:
            pendencias_preview.append({
                "numero": contador,
                "titulo": f"{contador}º Relatório Fiscal",
                "data_prazo": data_atual.isoformat(),
                "dias_desde_inicio": (data_atual - data_inicio).days,
                "dias_ate_fim": (data_fim - data_atual).days
            })

            data_atual += timedelta(days=intervalo_dias)
            contador += 1

        # Se não houver nenhuma pendência, retorna erro informativo
        if not pendencias_preview:
            duracao_contrato = (data_fim - data_inicio).days
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nenhuma pendência pode ser gerada. O contrato tem duração de {duracao_contrato} dias, "
                       f"menor que o intervalo configurado de {intervalo_dias} dias. "
                       f"Considere diminuir o intervalo ou criar pendências manualmente."
            )

        return {
            "contrato_id": contrato_id,
            "contrato_numero": contrato.get('nr_contrato'),
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
            "duracao_dias": (data_fim - data_inicio).days,
            "intervalo_dias": intervalo_dias,
            "total_pendencias": len(pendencias_preview),
            "pendencias": pendencias_preview
        }

    async def criar_pendencias_automaticas(
        self,
        contrato_id: int,
        criado_por_usuario_id: int,
        descricao_base: str = "Relatório fiscal periódico do contrato."
    ) -> List[Dict[str, Any]]:
        """
        Cria as pendências automáticas para um contrato.
        Deve ser chamado após o admin aprovar o preview.
        """
        from app.repositories.pendencia_repo import PendenciaRepository
        from app.schemas.pendencia_schema import PendenciaCreate

        # Calcula o preview primeiro
        preview = await self.calcular_pendencias_automaticas(contrato_id)

        # Busca o status "Pendente"
        all_status = await self.status_pendencia_repo.get_all()
        status_pendente = next((s for s in all_status if s['nome'] == 'Pendente'), None)

        if not status_pendente:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Status 'Pendente' não encontrado no sistema"
            )

        # Cria as pendências
        pendencias_criadas = []
        pendencia_repo = PendenciaRepository(self.contrato_repo.conn)

        for pendencia_data in preview['pendencias']:
            pendencia_create = PendenciaCreate(
                titulo=pendencia_data['titulo'],
                descricao=descricao_base,
                data_prazo=pendencia_data['data_prazo'],
                status_pendencia_id=status_pendente['id'],
                criado_por_usuario_id=criado_por_usuario_id
            )

            nova_pendencia = await pendencia_repo.create_pendencia(contrato_id, pendencia_create)
            pendencias_criadas.append(nova_pendencia)

            print(f"✅ Pendência automática criada: {nova_pendencia['titulo']} - Prazo: {nova_pendencia['data_prazo']}")

        # Enviar emails de notificação para o fiscal e fiscal substituto
        try:
            print(f"📧 Iniciando envio de emails para pendências automáticas do contrato {contrato_id}...")
            contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)
            if contrato:
                print(f"📋 Contrato encontrado: {contrato.get('nr_contrato')} - Fiscal ID: {contrato.get('fiscal_id')} - Fiscal Sub ID: {contrato.get('fiscal_substituto_id')}")

                from app.repositories.usuario_repo import UsuarioRepository
                from app.services.email_service import EmailService
                from app.services.email_templates import EmailTemplates

                usuario_repo = UsuarioRepository(self.contrato_repo.conn)

                # Preparar resumo das pendências para o email
                resumo_pendencias = "\n".join([
                    f"• {p['titulo']} - Prazo: {p['data_prazo'].strftime('%d/%m/%Y') if isinstance(p['data_prazo'], date) else date.fromisoformat(p['data_prazo']).strftime('%d/%m/%Y')}"
                    for p in pendencias_criadas
                ])
                print(f"📝 Resumo de {len(pendencias_criadas)} pendências preparado")

                # Email para o fiscal principal
                if contrato.get('fiscal_id'):
                    print(f"👤 Buscando dados do fiscal principal (ID: {contrato.get('fiscal_id')})...")
                    fiscal = await usuario_repo.get_user_by_id(contrato['fiscal_id'])
                    if fiscal:
                        print(f"✅ Fiscal encontrado: {fiscal.get('nome')} ({fiscal.get('email')})")
                        subject = f"🔔 {len(pendencias_criadas)} Pendências Automáticas Criadas - Contrato {contrato['nr_contrato']}"
                        body = f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #2563eb;">Olá, {fiscal['nome']}!</h2>
                            <p>Foram criadas <strong>{len(pendencias_criadas)} pendências automáticas</strong> para o contrato:</p>

                            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                <p><strong>Contrato:</strong> {contrato['nr_contrato']}</p>
                                <p><strong>Objeto:</strong> {contrato.get('objeto', 'N/A')}</p>
                                <p><strong>Período:</strong> {date.fromisoformat(contrato['data_inicio']).strftime('%d/%m/%Y')} até {date.fromisoformat(contrato['data_fim']).strftime('%d/%m/%Y')}</p>
                            </div>

                            <h3 style="color: #2563eb;">Pendências Criadas:</h3>
                            <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                                <pre style="margin: 0; white-space: pre-wrap;">{resumo_pendencias}</pre>
                            </div>

                            <p style="margin-top: 20px;">Por favor, fique atento aos prazos e envie os relatórios fiscais dentro do prazo estabelecido.</p>

                            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                                Este é um email automático do SIGESCON. Não responda a este email.
                            </p>
                        </div>
                        """
                        print(f"📤 Enviando email para fiscal principal...")
                        await EmailService.send_email(fiscal['email'], subject, body, is_html=True)
                        print(f"✅ Email de pendências automáticas enviado para o fiscal principal: {fiscal['email']}")

                        # Delay de 30 segundos entre envios para evitar bloqueio do provedor
                        print(f"⏳ Aguardando 30 segundos antes do próximo envio...")
                        await asyncio.sleep(30)
                    else:
                        print(f"⚠️ Fiscal principal não encontrado no banco de dados")
                else:
                    print(f"⚠️ Contrato sem fiscal principal associado")

                # Email para o fiscal substituto
                if contrato.get('fiscal_substituto_id'):
                    print(f"👤 Buscando dados do fiscal substituto (ID: {contrato.get('fiscal_substituto_id')})...")
                    fiscal_sub = await usuario_repo.get_user_by_id(contrato['fiscal_substituto_id'])
                    if fiscal_sub:
                        print(f"✅ Fiscal substituto encontrado: {fiscal_sub.get('nome')} ({fiscal_sub.get('email')})")
                        subject = f"🔔 {len(pendencias_criadas)} Pendências Automáticas Criadas - Contrato {contrato['nr_contrato']}"
                        body = f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #2563eb;">Olá, {fiscal_sub['nome']}!</h2>
                            <p>Foram criadas <strong>{len(pendencias_criadas)} pendências automáticas</strong> para o contrato onde você é fiscal substituto:</p>

                            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                <p><strong>Contrato:</strong> {contrato['nr_contrato']}</p>
                                <p><strong>Objeto:</strong> {contrato.get('objeto', 'N/A')}</p>
                                <p><strong>Período:</strong> {date.fromisoformat(contrato['data_inicio']).strftime('%d/%m/%Y')} até {date.fromisoformat(contrato['data_fim']).strftime('%d/%m/%Y')}</p>
                            </div>

                            <h3 style="color: #2563eb;">Pendências Criadas:</h3>
                            <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                                <pre style="margin: 0; white-space: pre-wrap;">{resumo_pendencias}</pre>
                            </div>

                            <p style="margin-top: 20px;">Como fiscal substituto, você também deve estar ciente destes prazos.</p>

                            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                                Este é um email automático do SIGESCON. Não responda a este email.
                            </p>
                        </div>
                        """
                        print(f"📤 Enviando email para fiscal substituto...")
                        await EmailService.send_email(fiscal_sub['email'], subject, body, is_html=True)
                        print(f"✅ Email de pendências automáticas enviado para o fiscal substituto: {fiscal_sub['email']}")
                    else:
                        print(f"⚠️ Fiscal substituto não encontrado no banco de dados")
                else:
                    print(f"⚠️ Contrato sem fiscal substituto associado")
            else:
                print(f"⚠️ Contrato não encontrado após criação das pendências")

        except Exception as e:
            print(f"❌ ERRO ao enviar emails de notificação de pendências automáticas: {e}")
            print(f"❌ Tipo do erro: {type(e).__name__}")
            import traceback
            print(f"❌ Traceback completo:\n{traceback.format_exc()}")
            # Não falha a criação das pendências por erro no email

        return pendencias_criadas
