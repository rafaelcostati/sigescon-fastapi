# app/services/email_templates.py
from typing import Dict, Optional
from datetime import date

class EmailTemplates:
    """Templates padronizados para emails do sistema"""
    
    @staticmethod
    def contract_assignment_fiscal(fiscal_nome: str, contrato_data: Dict, is_new: bool = True) -> tuple[str, str]:
        """Template para notificar fiscal sobre atribuição de contrato"""
        action = "atribuído" if is_new else "atualizado"
        subject = f"Contrato {action}: {contrato_data['nr_contrato']}"
        
        # Formatação de valores
        valor_anual = f"R$ {contrato_data.get('valor_anual', 0):,.2f}" if contrato_data.get('valor_anual') else "Não informado"
        valor_global = f"R$ {contrato_data.get('valor_global', 0):,.2f}" if contrato_data.get('valor_global') else "Não informado"
        
        body = f"""
Olá, {fiscal_nome},

Você foi designado como fiscal responsável pelo contrato:

📋 DETALHES DO CONTRATO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Número: {contrato_data['nr_contrato']}
• Objeto: {contrato_data['objeto']}
• Período: {contrato_data['data_inicio']} até {contrato_data['data_fim']}
• Valor Anual: {valor_anual}
• Valor Global: {valor_global}
• Contratado: {contrato_data.get('contratado_nome', 'Não informado')}
• Modalidade: {contrato_data.get('modalidade_nome', 'Não informada')}

👨‍💼 SUAS RESPONSABILIDADES COMO FISCAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Acompanhar a execução do contrato
✅ Verificar o cumprimento das obrigações contratuais
✅ Submeter relatórios fiscais quando solicitado
✅ Monitorar prazos e responder às pendências
✅ Comunicar irregularidades aos gestores

🔗 PRÓXIMOS PASSOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Acesse o sistema SIGESCON para:
• Visualizar todos os detalhes do contrato
• Consultar documentos anexos
• Acompanhar pendências ativas

Atenciosamente,
Sistema SIGESCON - Gestão de Contratos
        """
        return subject, body

    @staticmethod
    def contract_assignment_manager(gestor_nome: str, contrato_data: Dict, fiscal_data: Optional[Dict] = None, is_new: bool = True) -> tuple[str, str]:
        """Template para notificar gestor sobre atribuição de contrato"""
        action = "criado" if is_new else "atualizado"
        subject = f"Contrato {action} sob sua gestão: {contrato_data['nr_contrato']}"
        
        # Formatação de valores
        valor_anual = f"R$ {contrato_data.get('valor_anual', 0):,.2f}" if contrato_data.get('valor_anual') else "Não informado"
        valor_global = f"R$ {contrato_data.get('valor_global', 0):,.2f}" if contrato_data.get('valor_global') else "Não informado"
        
        # Informações do fiscal
        fiscal_info = ""
        if fiscal_data:
            fiscal_info = f"\n• Fiscal Responsável: {fiscal_data['nome']} ({fiscal_data['email']})"
        
        body = f"""
Olá, {gestor_nome},

Um contrato sob sua gestão foi {action}:

📋 DETALHES DO CONTRATO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Número: {contrato_data['nr_contrato']}
• Objeto: {contrato_data['objeto']}
• Período: {contrato_data['data_inicio']} até {contrato_data['data_fim']}
• Valor Anual: {valor_anual}
• Valor Global: {valor_global}
• Contratado: {contrato_data.get('contratado_nome', 'Não informado')}
• Modalidade: {contrato_data.get('modalidade_nome', 'Não informada')}{fiscal_info}

👨‍💼 SUAS RESPONSABILIDADES COMO GESTOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Supervisionar a execução geral do contrato
✅ Coordenar as atividades de fiscalização
✅ Analisar e aprovar relatórios fiscais
✅ Gerenciar pendências e prazos
✅ Tomar decisões estratégicas sobre o contrato

🔗 PRÓXIMOS PASSOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Acesse o sistema SIGESCON para:
• Visualizar detalhes completos do contrato
• Acompanhar relatórios e pendências
• Gerenciar toda a operação

Atenciosamente,
Sistema SIGESCON - Gestão de Contratos
        """
        return subject, body

    @staticmethod
    def contract_transfer_notification(fiscal_nome: str, contrato_data: Dict, novo_fiscal_nome: Optional[str] = None) -> tuple[str, str]:
        """Template para notificar fiscal sobre transferência de contrato"""
        subject = f"Contrato transferido: {contrato_data['nr_contrato']}"
        
        transfer_info = ""
        if novo_fiscal_nome:
            transfer_info = f"\nA responsabilidade foi transferida para: {novo_fiscal_nome}"
        
        body = f"""
Olá, {fiscal_nome},

Informamos que você não é mais o fiscal responsável pelo contrato:

📋 DETALHES DO CONTRATO TRANSFERIDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Número: {contrato_data['nr_contrato']}
• Objeto: {contrato_data['objeto']}
• Período: {contrato_data['data_inicio']} até {contrato_data['data_fim']}
• Contratado: {contrato_data.get('contratado_nome', 'Não informado')}{transfer_info}

🙏 AGRADECIMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agradecemos pelo trabalho realizado durante o período de sua responsabilidade.
Sua dedicação foi fundamental para o bom andamento do contrato.

Quaisquer pendências ou relatórios em andamento serão transferidos
para o novo fiscal responsável.

Atenciosamente,
Sistema SIGESCON - Gestão de Contratos
        """
        return subject, body

    @staticmethod
    def pending_report_notification(fiscal_nome: str, contrato_data: Dict, pendencia_data: Dict) -> tuple[str, str]:
        """Template para notificar sobre nova pendência (já existente, mantido para compatibilidade)"""
        subject = f"Nova pendência: Contrato {contrato_data['nr_contrato']}"
        
        # Calcula dias até o prazo
        prazo = pendencia_data['data_prazo']
        if isinstance(prazo, str):
            from datetime import datetime
            prazo = datetime.strptime(prazo, '%Y-%m-%d').date()
        
        dias_restantes = (prazo - date.today()).days
        urgencia_texto = ""
        if dias_restantes <= 1:
            urgencia_texto = " ⚠️ URGENTE!"
        elif dias_restantes <= 3:
            urgencia_texto = " ⏰ Atenção!"
        
        body = f"""
Olá, {fiscal_nome},

Uma nova pendência foi criada para você no contrato{urgencia_texto}

📋 DETALHES DA PENDÊNCIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Contrato: {contrato_data['nr_contrato']}
• Objeto: {contrato_data['objeto']}
• Descrição: {pendencia_data.get('descricao', 'N/A')}
• Prazo: {prazo.strftime('%d/%m/%Y')} ({dias_restantes} dias restantes)

🔗 AÇÃO NECESSÁRIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Por favor, acesse o sistema SIGESCON para submeter o relatório solicitado
dentro do prazo estabelecido.

Atenciosamente,
Sistema SIGESCON - Gestão de Contratos
        """
        return subject, body

    @staticmethod
    def pending_cancellation_notification(fiscal_nome: str, contrato_data: Dict, pendencia_data: Dict) -> tuple[str, str]:
        """Template para notificar fiscal sobre cancelamento de pendência"""
        subject = f"Pendência cancelada: Contrato {contrato_data['nr_contrato']}"

        body = f"""
Olá, {fiscal_nome},

Uma pendência do contrato foi cancelada pelo administrador.

📋 DETALHES DA PENDÊNCIA CANCELADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Contrato: {contrato_data['nr_contrato']}
• Objeto: {contrato_data['objeto']}
• Descrição: {pendencia_data.get('descricao', 'N/A')}
• Status: CANCELADA

✅ NENHUMA AÇÃO NECESSÁRIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Você não precisa mais enviar relatório para esta pendência.
A solicitação foi cancelada pela administração.

Atenciosamente,
Sistema SIGESCON - Gestão de Contratos
        """
        return subject, body

    @staticmethod
    def report_submitted_notification(admin_nome: str, contrato_data: Dict, pendencia_data: Dict, fiscal_data: Dict) -> tuple[str, str]:
        """Template para notificar administrador sobre relatório submetido"""
        subject = f"Relatório submetido: Contrato {contrato_data['nr_contrato']}"

        body = f"""
Olá, {admin_nome},

Um novo relatório foi submetido e aguarda sua análise.

📋 DETALHES DO RELATÓRIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Contrato: {contrato_data['nr_contrato']}
• Objeto: {contrato_data['objeto']}
• Fiscal: {fiscal_data['nome']} ({fiscal_data['email']})
• Pendência: {pendencia_data.get('descricao', 'N/A')}
• Status: Pendente de Análise

🔗 AÇÃO NECESSÁRIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Acesse o sistema SIGESCON para analisar o relatório submetido
e decidir entre aprovar ou rejeitar.

Atenciosamente,
Sistema SIGESCON - Gestão de Contratos
        """
        return subject, body

    @staticmethod
    def report_approved_notification(fiscal_nome: str, contrato_data: Dict, pendencia_data: Dict) -> tuple[str, str]:
        """Template para notificar fiscal sobre relatório aprovado"""
        subject = f"Relatório aprovado: Contrato {contrato_data['nr_contrato']}"

        body = f"""
Olá, {fiscal_nome},

Seu relatório foi APROVADO pelo administrador.

📋 DETALHES DO RELATÓRIO APROVADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Contrato: {contrato_data['nr_contrato']}
• Objeto: {contrato_data['objeto']}
• Pendência: {pendencia_data.get('descricao', 'N/A')}
• Status: APROVADO ✅

🎉 PARABÉNS!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Seu relatório atendeu aos requisitos e foi aprovado.
A pendência foi marcada como concluída.

Atenciosamente,
Sistema SIGESCON - Gestão de Contratos
        """
        return subject, body

    @staticmethod
    def report_rejected_notification(fiscal_nome: str, contrato_data: Dict, pendencia_data: Dict, observacoes: str = None) -> tuple[str, str]:
        """Template para notificar fiscal sobre relatório rejeitado"""
        subject = f"Relatório rejeitado: Contrato {contrato_data['nr_contrato']}"

        observacoes_section = ""
        if observacoes:
            observacoes_section = f"""
🔍 OBSERVAÇÕES DO ADMINISTRADOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{observacoes}
"""

        body = f"""
Olá, {fiscal_nome},

Seu relatório foi REJEITADO e necessita de correções.

📋 DETALHES DO RELATÓRIO REJEITADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Contrato: {contrato_data['nr_contrato']}
• Objeto: {contrato_data['objeto']}
• Pendência: {pendencia_data.get('descricao', 'N/A')}
• Status: REJEITADO ❌{observacoes_section}

🔄 AÇÃO NECESSÁRIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Por favor, faça as correções necessárias e reenvie o relatório
através do sistema SIGESCON.

Atenciosamente,
Sistema SIGESCON - Gestão de Contratos
        """
        return subject, body