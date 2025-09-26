# app/services/email_templates.py
from typing import Dict, Optional
from datetime import date

class EmailTemplates:
    """Templates padronizados para emails do sistema"""
    
    @staticmethod
    def contract_assignment_fiscal(fiscal_nome: str, contrato_data: Dict, is_new: bool = True) -> tuple[str, str]:
        """Template para notificar fiscal sobre atribuição de contrato"""
        action = "atribuído" if is_new else "atualizado"
        subject = f"📋 Contrato {action}: {contrato_data['nr_contrato']} - SIGESCON"

        # Formatação de valores
        valor_anual = f"R$ {contrato_data.get('valor_anual', 0):,.2f}" if contrato_data.get('valor_anual') else "Não informado"
        valor_global = f"R$ {contrato_data.get('valor_global', 0):,.2f}" if contrato_data.get('valor_global') else "Não informado"

        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atribuição de Contrato - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #495057;
        }}
        .section {{
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .section-title .icon {{
            margin-right: 8px;
            font-size: 18px;
        }}
        .detail-item {{
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #495057;
            display: inline-block;
            min-width: 120px;
        }}
        .detail-value {{
            color: #212529;
        }}
        .responsibilities {{
            background-color: #e8f5e8;
            border-left: 4px solid #28a745;
        }}
        .responsibility-item {{
            margin: 8px 0;
            padding-left: 20px;
            position: relative;
        }}
        .responsibility-item:before {{
            content: "✅";
            position: absolute;
            left: 0;
        }}
        .action-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }}
        .action-title {{
            font-weight: bold;
            color: #856404;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .action-item {{
            margin: 8px 0;
            color: #856404;
            padding-left: 20px;
            position: relative;
        }}
        .action-item:before {{
            content: "•";
            position: absolute;
            left: 0;
            font-weight: bold;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">📋 SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="greeting">
            Olá <strong>{fiscal_nome}</strong>,
        </div>

        <p>Você foi designado como <strong>fiscal responsável</strong> pelo contrato abaixo:</p>

        <div class="section">
            <div class="section-title">
                <span class="icon">📋</span> DETALHES DO CONTRATO
            </div>
            <div class="detail-item">
                <span class="detail-label">Número:</span>
                <span class="detail-value">{contrato_data['nr_contrato']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Objeto:</span>
                <span class="detail-value">{contrato_data['objeto']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Período:</span>
                <span class="detail-value">{contrato_data['data_inicio']} até {contrato_data['data_fim']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Valor Anual:</span>
                <span class="detail-value">{valor_anual}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Valor Global:</span>
                <span class="detail-value">{valor_global}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Contratado:</span>
                <span class="detail-value">{contrato_data.get('contratado_nome', 'Não informado')}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Modalidade:</span>
                <span class="detail-value">{contrato_data.get('modalidade_nome', 'Não informada')}</span>
            </div>
        </div>

        <div class="section responsibilities">
            <div class="section-title">
                <span class="icon">👨‍💼</span> SUAS RESPONSABILIDADES COMO FISCAL
            </div>
            <div class="responsibility-item">Acompanhar a execução do contrato</div>
            <div class="responsibility-item">Verificar o cumprimento das obrigações contratuais</div>
            <div class="responsibility-item">Submeter relatórios fiscais quando solicitado</div>
            <div class="responsibility-item">Monitorar prazos e responder às pendências</div>
            <div class="responsibility-item">Comunicar irregularidades aos gestores</div>
        </div>

        <div class="action-box">
            <div class="action-title">
                <span class="icon">🔗</span> PRÓXIMOS PASSOS
            </div>
            <div>Acesse o sistema SIGESCON para:</div>
            <div class="action-item">Visualizar todos os detalhes do contrato</div>
            <div class="action-item">Consultar documentos anexos</div>
            <div class="action-item">Acompanhar pendências ativas</div>
        </div>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """
        return subject, body

    @staticmethod
    def contract_assignment_manager(gestor_nome: str, contrato_data: Dict, fiscal_data: Optional[Dict] = None, is_new: bool = True) -> tuple[str, str]:
        """Template para notificar gestor sobre atribuição de contrato"""
        action = "criado" if is_new else "atualizado"
        subject = f"💼 Contrato {action} sob sua gestão: {contrato_data['nr_contrato']} - SIGESCON"

        # Formatação de valores
        valor_anual = f"R$ {contrato_data.get('valor_anual', 0):,.2f}" if contrato_data.get('valor_anual') else "Não informado"
        valor_global = f"R$ {contrato_data.get('valor_global', 0):,.2f}" if contrato_data.get('valor_global') else "Não informado"

        # Informações do fiscal
        fiscal_info_html = ""
        if fiscal_data:
            fiscal_info_html = f"""
            <div class="detail-item">
                <span class="detail-label">Fiscal Responsável:</span>
                <span class="detail-value">{fiscal_data['nome']} ({fiscal_data['email']})</span>
            </div>"""

        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contrato sob Gestão - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #495057;
        }}
        .section {{
            background-color: #f8f9fa;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #28a745;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .section-title .icon {{
            margin-right: 8px;
            font-size: 18px;
        }}
        .detail-item {{
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #495057;
            display: inline-block;
            min-width: 120px;
        }}
        .detail-value {{
            color: #212529;
        }}
        .responsibilities {{
            background-color: #e8f4fd;
            border-left: 4px solid #17a2b8;
        }}
        .responsibilities .section-title {{
            color: #17a2b8;
        }}
        .responsibility-item {{
            margin: 8px 0;
            padding-left: 20px;
            position: relative;
        }}
        .responsibility-item:before {{
            content: "✅";
            position: absolute;
            left: 0;
        }}
        .action-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }}
        .action-title {{
            font-weight: bold;
            color: #856404;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .action-item {{
            margin: 8px 0;
            color: #856404;
            padding-left: 20px;
            position: relative;
        }}
        .action-item:before {{
            content: "•";
            position: absolute;
            left: 0;
            font-weight: bold;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">💼 SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="greeting">
            Olá <strong>{gestor_nome}</strong>,
        </div>

        <p>Um contrato sob sua gestão foi <strong>{action}</strong>:</p>

        <div class="section">
            <div class="section-title">
                <span class="icon">📋</span> DETALHES DO CONTRATO
            </div>
            <div class="detail-item">
                <span class="detail-label">Número:</span>
                <span class="detail-value">{contrato_data['nr_contrato']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Objeto:</span>
                <span class="detail-value">{contrato_data['objeto']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Período:</span>
                <span class="detail-value">{contrato_data['data_inicio']} até {contrato_data['data_fim']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Valor Anual:</span>
                <span class="detail-value">{valor_anual}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Valor Global:</span>
                <span class="detail-value">{valor_global}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Contratado:</span>
                <span class="detail-value">{contrato_data.get('contratado_nome', 'Não informado')}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Modalidade:</span>
                <span class="detail-value">{contrato_data.get('modalidade_nome', 'Não informada')}</span>
            </div>{fiscal_info_html}
        </div>

        <div class="section responsibilities">
            <div class="section-title">
                <span class="icon">👨‍💼</span> SUAS RESPONSABILIDADES COMO GESTOR
            </div>
            <div class="responsibility-item">Supervisionar a execução geral do contrato</div>
            <div class="responsibility-item">Coordenar as atividades de fiscalização</div>
            <div class="responsibility-item">Analisar e aprovar relatórios fiscais</div>
            <div class="responsibility-item">Gerenciar pendências e prazos</div>
            <div class="responsibility-item">Tomar decisões estratégicas sobre o contrato</div>
        </div>

        <div class="action-box">
            <div class="action-title">
                <span class="icon">🔗</span> PRÓXIMOS PASSOS
            </div>
            <div>Acesse o sistema SIGESCON para:</div>
            <div class="action-item">Visualizar detalhes completos do contrato</div>
            <div class="action-item">Acompanhar relatórios e pendências</div>
            <div class="action-item">Gerenciar toda a operação</div>
        </div>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """
        return subject, body

    @staticmethod
    def contract_transfer_notification(fiscal_nome: str, contrato_data: Dict, novo_fiscal_nome: Optional[str] = None) -> tuple[str, str]:
        """Template para notificar fiscal sobre transferência de contrato"""
        subject = f"🔄 Contrato transferido: {contrato_data['nr_contrato']} - SIGESCON"

        transfer_info_html = ""
        if novo_fiscal_nome:
            transfer_info_html = f"""
            <div class="detail-item">
                <span class="detail-label">Novo Fiscal:</span>
                <span class="detail-value">{novo_fiscal_nome}</span>
            </div>"""

        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transferência de Contrato - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #495057;
        }}
        .section {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #856404;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .section-title .icon {{
            margin-right: 8px;
            font-size: 18px;
        }}
        .detail-item {{
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #f5e79e;
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #495057;
            display: inline-block;
            min-width: 120px;
        }}
        .detail-value {{
            color: #212529;
        }}
        .thanks-section {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .thanks-title {{
            font-size: 16px;
            font-weight: bold;
            color: #155724;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .thanks-content {{
            color: #155724;
            line-height: 1.6;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🔄 SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="greeting">
            Olá <strong>{fiscal_nome}</strong>,
        </div>

        <p>Informamos que você <strong>não é mais o fiscal responsável</strong> pelo contrato abaixo:</p>

        <div class="section">
            <div class="section-title">
                <span class="icon">📋</span> DETALHES DO CONTRATO TRANSFERIDO
            </div>
            <div class="detail-item">
                <span class="detail-label">Número:</span>
                <span class="detail-value">{contrato_data['nr_contrato']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Objeto:</span>
                <span class="detail-value">{contrato_data['objeto']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Período:</span>
                <span class="detail-value">{contrato_data['data_inicio']} até {contrato_data['data_fim']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Contratado:</span>
                <span class="detail-value">{contrato_data.get('contratado_nome', 'Não informado')}</span>
            </div>{transfer_info_html}
        </div>

        <div class="thanks-section">
            <div class="thanks-title">
                <span class="icon">🙏</span> AGRADECIMENTO
            </div>
            <div class="thanks-content">
                <p>Agradecemos pelo trabalho realizado durante o período de sua responsabilidade. Sua dedicação foi fundamental para o bom andamento do contrato.</p>
                <p>Quaisquer pendências ou relatórios em andamento serão transferidos para o novo fiscal responsável.</p>
            </div>
        </div>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """
        return subject, body

    @staticmethod
    def pending_report_notification(fiscal_nome: str, contrato_data: Dict, pendencia_data: Dict) -> tuple[str, str]:
        """Template para notificar sobre nova pendência (já existente, mantido para compatibilidade)"""

        # Calcula dias até o prazo
        prazo = pendencia_data['data_prazo']
        if isinstance(prazo, str):
            from datetime import datetime
            prazo = datetime.strptime(prazo, '%Y-%m-%d').date()

        dias_restantes = (prazo - date.today()).days
        urgencia_emoji = ""
        urgencia_class = "normal"
        urgencia_texto = ""

        if dias_restantes <= 1:
            urgencia_emoji = "😨"
            urgencia_class = "urgent"
            urgencia_texto = " - URGENTE!"
        elif dias_restantes <= 3:
            urgencia_emoji = "⚠️"
            urgencia_class = "warning"
            urgencia_texto = " - Atenção!"
        else:
            urgencia_emoji = "📋"
            urgencia_class = "normal"

        subject = f"{urgencia_emoji} Nova pendência: Contrato {contrato_data['nr_contrato']}{urgencia_texto} - SIGESCON"

        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nova Pendência - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #495057;
        }}
        .section {{
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .section.normal {{
            background-color: #e8f4fd;
            border-left: 4px solid #17a2b8;
        }}
        .section.warning {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
        }}
        .section.urgent {{
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .section-title.normal {{ color: #17a2b8; }}
        .section-title.warning {{ color: #856404; }}
        .section-title.urgent {{ color: #721c24; }}
        .section-title .icon {{
            margin-right: 8px;
            font-size: 18px;
        }}
        .detail-item {{
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #495057;
            display: inline-block;
            min-width: 100px;
        }}
        .detail-value {{
            color: #212529;
        }}
        .days-remaining {{
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 5px;
            display: inline-block;
        }}
        .days-remaining.normal {{
            background-color: #d1ecf1;
            color: #0c5460;
        }}
        .days-remaining.warning {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .days-remaining.urgent {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .action-box {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }}
        .action-title {{
            font-weight: bold;
            color: #155724;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .action-content {{
            color: #155724;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">{urgencia_emoji} SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="greeting">
            Olá <strong>{fiscal_nome}</strong>,
        </div>

        <p>Uma <strong>nova pendência</strong> foi criada para você no contrato:</p>

        <div class="section {urgencia_class}">
            <div class="section-title {urgencia_class}">
                <span class="icon">📋</span> DETALHES DA PENDÊNCIA
            </div>
            <div class="detail-item">
                <span class="detail-label">Contrato:</span>
                <span class="detail-value">{contrato_data['nr_contrato']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Objeto:</span>
                <span class="detail-value">{contrato_data['objeto']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Descrição:</span>
                <span class="detail-value">{pendencia_data.get('descricao', 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Prazo:</span>
                <span class="detail-value">{prazo.strftime('%d/%m/%Y')}</span>
            </div>
            <div style="text-align: center; margin-top: 15px;">
                <span class="days-remaining {urgencia_class}">
                    {dias_restantes} dias restantes
                </span>
            </div>
        </div>

        <div class="action-box">
            <div class="action-title">
                <span class="icon">🔗</span> AÇÃO NECESSÁRIA
            </div>
            <div class="action-content">
                Por favor, acesse o sistema SIGESCON para submeter o relatório solicitado dentro do prazo estabelecido.
            </div>
        </div>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """
        return subject, body

    @staticmethod
    def pending_cancellation_notification(fiscal_nome: str, contrato_data: Dict, pendencia_data: Dict) -> tuple[str, str]:
        """Template para notificar fiscal sobre cancelamento de pendência"""
        subject = f"✅ Pendência cancelada: Contrato {contrato_data['nr_contrato']} - SIGESCON"

        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pendência Cancelada - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #495057;
        }}
        .section {{
            background-color: #e2e3e5;
            border-left: 4px solid #6c757d;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .section-title .icon {{
            margin-right: 8px;
            font-size: 18px;
        }}
        .detail-item {{
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #adb5bd;
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #495057;
            display: inline-block;
            min-width: 100px;
        }}
        .detail-value {{
            color: #212529;
        }}
        .status-cancelled {{
            background-color: #6c757d;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
        }}
        .success-box {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }}
        .success-title {{
            font-weight: bold;
            color: #155724;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .success-content {{
            color: #155724;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">✅ SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="greeting">
            Olá <strong>{fiscal_nome}</strong>,
        </div>

        <p>Uma pendência do contrato foi <strong>cancelada pelo administrador</strong>.</p>

        <div class="section">
            <div class="section-title">
                <span class="icon">📋</span> DETALHES DA PENDÊNCIA CANCELADA
            </div>
            <div class="detail-item">
                <span class="detail-label">Contrato:</span>
                <span class="detail-value">{contrato_data['nr_contrato']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Objeto:</span>
                <span class="detail-value">{contrato_data['objeto']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Descrição:</span>
                <span class="detail-value">{pendencia_data.get('descricao', 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Status:</span>
                <span class="status-cancelled">CANCELADA</span>
            </div>
        </div>

        <div class="success-box">
            <div class="success-title">
                <span class="icon">✅</span> NENHUMA AÇÃO NECESSÁRIA
            </div>
            <div class="success-content">
                <p>Você <strong>não precisa mais enviar relatório</strong> para esta pendência.</p>
                <p>A solicitação foi cancelada pela administração.</p>
            </div>
        </div>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """
        return subject, body

    @staticmethod
    def report_submitted_notification(admin_nome: str, contrato_data: Dict, pendencia_data: Dict, fiscal_data: Dict) -> tuple[str, str]:
        """Template para notificar administrador sobre relatório submetido"""
        subject = f"📄 Relatório submetido: Contrato {contrato_data['nr_contrato']} - SIGESCON"

        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Submetido - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #495057;
        }}
        .section {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #856404;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .section-title .icon {{
            margin-right: 8px;
            font-size: 18px;
        }}
        .detail-item {{
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #f5e79e;
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #495057;
            display: inline-block;
            min-width: 100px;
        }}
        .detail-value {{
            color: #212529;
        }}
        .status-pending {{
            background-color: #ffc107;
            color: #212529;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
        }}
        .action-box {{
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }}
        .action-title {{
            font-weight: bold;
            color: #0c5460;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .action-content {{
            color: #0c5460;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">📄 SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="greeting">
            Olá <strong>{admin_nome}</strong>,
        </div>

        <p>Um <strong>novo relatório foi submetido</strong> e aguarda sua análise.</p>

        <div class="section">
            <div class="section-title">
                <span class="icon">📋</span> DETALHES DO RELATÓRIO
            </div>
            <div class="detail-item">
                <span class="detail-label">Contrato:</span>
                <span class="detail-value">{contrato_data['nr_contrato']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Objeto:</span>
                <span class="detail-value">{contrato_data['objeto']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Fiscal:</span>
                <span class="detail-value">{fiscal_data['nome']} ({fiscal_data['email']})</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Pendência:</span>
                <span class="detail-value">{pendencia_data.get('descricao', 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Status:</span>
                <span class="status-pending">Pendente de Análise</span>
            </div>
        </div>

        <div class="action-box">
            <div class="action-title">
                <span class="icon">🔗</span> AÇÃO NECESSÁRIA
            </div>
            <div class="action-content">
                Acesse o sistema SIGESCON para analisar o relatório submetido e decidir entre <strong>aprovar</strong> ou <strong>rejeitar</strong>.
            </div>
        </div>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """
        return subject, body

    @staticmethod
    def report_approved_notification(fiscal_nome: str, contrato_data: Dict, pendencia_data: Dict) -> tuple[str, str]:
        """Template para notificar fiscal sobre relatório aprovado"""
        subject = f"✅ Relatório aprovado: Contrato {contrato_data['nr_contrato']} - SIGESCON"

        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Aprovado - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #495057;
        }}
        .success-badge {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .success-title {{
            font-size: 20px;
            font-weight: bold;
            color: #155724;
            margin-bottom: 10px;
        }}
        .section {{
            background-color: #e8f5e8;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #155724;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .section-title .icon {{
            margin-right: 8px;
            font-size: 18px;
        }}
        .detail-item {{
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #c3e6cb;
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #495057;
            display: inline-block;
            min-width: 100px;
        }}
        .detail-value {{
            color: #212529;
        }}
        .status-approved {{
            background-color: #28a745;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
        }}
        .congratulations-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .congratulations-title {{
            font-weight: bold;
            color: #856404;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .congratulations-content {{
            color: #856404;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">✅ SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="greeting">
            Olá <strong>{fiscal_nome}</strong>,
        </div>

        <div class="success-badge">
            <div class="success-title">🎉 Seu relatório foi APROVADO!</div>
            <p>Parabéns pelo excelente trabalho!</p>
        </div>

        <div class="section">
            <div class="section-title">
                <span class="icon">📋</span> DETALHES DO RELATÓRIO APROVADO
            </div>
            <div class="detail-item">
                <span class="detail-label">Contrato:</span>
                <span class="detail-value">{contrato_data['nr_contrato']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Objeto:</span>
                <span class="detail-value">{contrato_data['objeto']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Pendência:</span>
                <span class="detail-value">{pendencia_data.get('descricao', 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Status:</span>
                <span class="status-approved">APROVADO ✅</span>
            </div>
        </div>

        <div class="congratulations-box">
            <div class="congratulations-title">🎉 PARABÉNS!</div>
            <div class="congratulations-content">
                <p>Seu relatório atendeu aos requisitos e foi aprovado pelo administrador.</p>
                <p>A pendência foi marcada como <strong>concluída</strong>.</p>
            </div>
        </div>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """
        return subject, body

    @staticmethod
    def report_rejected_notification(fiscal_nome: str, contrato_data: Dict, pendencia_data: Dict, observacoes: str = None) -> tuple[str, str]:
        """Template para notificar fiscal sobre relatório rejeitado"""
        subject = f"❌ Relatório rejeitado: Contrato {contrato_data['nr_contrato']} - SIGESCON"

        observacoes_section_html = ""
        if observacoes:
            observacoes_section_html = f"""
        <div class="observations-box">
            <div class="observations-title">
                <span class="icon">🔍</span> OBSERVAÇÕES DO ADMINISTRADOR
            </div>
            <div class="observations-content">
                {observacoes}
            </div>
        </div>"""

        body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Rejeitado - SIGESCON</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #495057;
        }}
        .rejection-badge {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .rejection-title {{
            font-size: 18px;
            font-weight: bold;
            color: #721c24;
            margin-bottom: 10px;
        }}
        .section {{
            background-color: #fff5f5;
            border-left: 4px solid #dc3545;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #721c24;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .section-title .icon {{
            margin-right: 8px;
            font-size: 18px;
        }}
        .detail-item {{
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #f5c6cb;
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #495057;
            display: inline-block;
            min-width: 100px;
        }}
        .detail-value {{
            color: #212529;
        }}
        .status-rejected {{
            background-color: #dc3545;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
        }}
        .observations-box {{
            background-color: #e2e3e5;
            border: 1px solid #adb5bd;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }}
        .observations-title {{
            font-weight: bold;
            color: #495057;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .observations-content {{
            color: #212529;
            background-color: #ffffff;
            padding: 15px;
            border-radius: 5px;
            border-left: 3px solid #6c757d;
        }}
        .action-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }}
        .action-title {{
            font-weight: bold;
            color: #856404;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .action-content {{
            color: #856404;
        }}
        .footer {{
            border-top: 2px solid #e9ecef;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">❌ SIGESCON</div>
            <div class="subtitle">Sistema de Gestão de Contratos</div>
        </div>

        <div class="greeting">
            Olá <strong>{fiscal_nome}</strong>,
        </div>

        <div class="rejection-badge">
            <div class="rejection-title">❌ Seu relatório foi rejeitado</div>
            <p>Necessita de correções antes da aprovação</p>
        </div>

        <div class="section">
            <div class="section-title">
                <span class="icon">📋</span> DETALHES DO RELATÓRIO REJEITADO
            </div>
            <div class="detail-item">
                <span class="detail-label">Contrato:</span>
                <span class="detail-value">{contrato_data['nr_contrato']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Objeto:</span>
                <span class="detail-value">{contrato_data['objeto']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Pendência:</span>
                <span class="detail-value">{pendencia_data.get('descricao', 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Status:</span>
                <span class="status-rejected">REJEITADO ❌</span>
            </div>
        </div>

        {observacoes_section_html}

        <div class="action-box">
            <div class="action-title">
                <span class="icon">🔄</span> AÇÃO NECESSÁRIA
            </div>
            <div class="action-content">
                Por favor, faça as <strong>correções necessárias</strong> e reenvie o relatório através do sistema SIGESCON.
            </div>
        </div>

        <div class="footer">
            <strong>Sistema de Gestão de Contratos - SIGESCON</strong><br>
            Este é um email automático, não responda.
        </div>
    </div>
</body>
</html>
        """
        return subject, body