# tests/test_email_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.email_service import EmailService
from app.services.email_templates import EmailTemplates
import asyncio

# --- Testes do Sistema de Notificações e Email ---

@pytest.mark.asyncio
async def test_email_service_static_method():
    """Testa se o método send_email é estático e funcionalmente acessível."""

    # EmailService tem método estático send_email
    assert hasattr(EmailService, 'send_email')
    assert callable(EmailService.send_email)

@pytest.mark.asyncio
async def test_email_templates_structure():
    """Testa se os templates de email estão estruturados corretamente."""

    templates = EmailTemplates()

    # Verificar se os métodos principais existem
    assert hasattr(templates, 'pending_report_notification')
    assert hasattr(templates, 'pending_cancellation_notification')
    assert hasattr(templates, 'report_submitted_notification')
    assert hasattr(templates, 'report_approved_notification')
    assert hasattr(templates, 'report_rejected_notification')
    assert hasattr(templates, 'contract_assignment_fiscal')
    assert hasattr(templates, 'contract_assignment_manager')

    # Testar template de atribuição de contrato fiscal
    subject, body = templates.contract_assignment_fiscal(
        fiscal_nome="João Silva",
        contrato_data={
            'nr_contrato': '001/2025',
            'objeto': 'Serviços de limpeza',
            'data_inicio': '2025-01-01',
            'data_fim': '2025-12-31',
            'contratado_nome': 'Empresa XYZ',
            'modalidade_nome': 'Pregão Eletrônico'
        }
    )

    assert isinstance(subject, str)
    assert isinstance(body, str)
    assert "João Silva" in body
    assert "001/2025" in body

@pytest.mark.asyncio
async def test_email_service_send_mock():
    """Testa o envio de email com mock."""

    with patch('aiosmtplib.send') as mock_send:
        mock_send.return_value = None

        # Simular envio de email usando método estático
        await EmailService.send_email(
            to_email="teste@exemplo.com",
            subject="Teste",
            body="Corpo do email de teste"
        )

        # Verificar se o mock foi chamado
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_notification_workflow_pendencia():
    """Testa o fluxo de notificação para criação de pendência."""

    with patch('aiosmtplib.send') as mock_send:
        mock_send.return_value = None

        templates = EmailTemplates()

        # Dados da pendência
        contrato_data = {
            "nr_contrato": "001/2025",
            "objeto": "Serviços de teste",
            "data_inicio": "2025-01-01",
            "data_fim": "2025-12-31"
        }

        pendencia_data = {
            "descricao": "Relatório de janeiro",
            "data_prazo": "2025-02-28"
        }

        # Gerar template
        subject, body = templates.pending_report_notification(
            fiscal_nome="João Fiscal",
            contrato_data=contrato_data,
            pendencia_data=pendencia_data
        )

        # Enviar email
        await EmailService.send_email(
            to_email="fiscal@teste.com",
            subject=subject,
            body=body
        )

        # Verificar se foi enviado
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_notification_workflow_relatorio():
    """Testa o fluxo de notificação para submissão de relatório."""

    with patch('aiosmtplib.send') as mock_send:
        mock_send.return_value = None

        templates = EmailTemplates()

        # Dados do relatório
        contrato_data = {
            "nr_contrato": "002/2025",
            "objeto": "Serviços de limpeza"
        }

        pendencia_data = {
            "descricao": "Relatório mensal"
        }

        fiscal_data = {
            "nome": "Maria Fiscal",
            "email": "maria@teste.com"
        }

        # Gerar template
        subject, body = templates.report_submitted_notification(
            admin_nome="Admin Sistema",
            contrato_data=contrato_data,
            pendencia_data=pendencia_data,
            fiscal_data=fiscal_data
        )

        # Enviar email
        await EmailService.send_email(
            to_email="admin@teste.com",
            subject=subject,
            body=body
        )

        # Verificar se foi enviado
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_email_service_error_handling():
    """Testa tratamento de erros no serviço de email."""

    with patch('aiosmtplib.send') as mock_send:
        # Simular erro de conexão
        mock_send.side_effect = Exception("Falha na conexão SMTP")

        # Tentar enviar email - o serviço deve capturar o erro sem quebrar
        await EmailService.send_email(
            to_email="teste@exemplo.com",
            subject="Teste",
            body="Corpo do teste"
        )

        # Verificar se o mock foi chamado (tentou enviar)
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_all_email_templates():
    """Testa todos os templates de email disponíveis."""

    templates = EmailTemplates()

    # Dados de teste padrão
    contrato_data = {
        "nr_contrato": "001/2025",
        "objeto": "Serviços de teste",
        "data_inicio": "2025-01-01",
        "data_fim": "2025-12-31",
        "contratado_nome": "Empresa Teste",
        "modalidade_nome": "Pregão"
    }

    pendencia_data = {
        "descricao": "Relatório mensal",
        "data_prazo": "2025-12-31"
    }

    fiscal_data = {
        "nome": "João Teste",
        "email": "joao@teste.com"
    }

    # Testar todos os templates principais
    templates_results = [
        templates.contract_assignment_fiscal("João Teste", contrato_data),
        templates.contract_assignment_manager("Admin Teste", contrato_data, fiscal_data),
        templates.pending_report_notification("João Teste", contrato_data, pendencia_data),
        templates.pending_cancellation_notification("João Teste", contrato_data, pendencia_data),
        templates.report_submitted_notification("Admin Teste", contrato_data, pendencia_data, fiscal_data),
        templates.report_approved_notification("João Teste", contrato_data, pendencia_data),
        templates.report_rejected_notification("João Teste", contrato_data, pendencia_data, "Observações de teste")
    ]

    # Verificar estrutura de todos os templates
    for subject, body in templates_results:
        assert isinstance(subject, str)
        assert isinstance(body, str)
        assert len(subject) > 0
        assert len(body) > 0
        assert "001/2025" in body