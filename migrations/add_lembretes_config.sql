-- Script para adicionar configurações de lembretes de pendências
-- Execute este script para criar as novas configurações no banco de dados

-- Insere a configuração de quantos dias antes do vencimento começar a enviar lembretes
INSERT INTO configuracao_sistema (chave, valor, descricao, tipo, created_at, updated_at)
VALUES (
    'lembretes_dias_antes_vencimento_inicio',
    '30',
    'Quantos dias antes do vencimento da pendência começar a enviar lembretes por email aos fiscais',
    'integer',
    NOW(),
    NOW()
)
ON CONFLICT (chave) DO NOTHING;

-- Insere a configuração de intervalo entre lembretes
INSERT INTO configuracao_sistema (chave, valor, descricao, tipo, created_at, updated_at)
VALUES (
    'lembretes_intervalo_dias',
    '5',
    'A cada quantos dias enviar lembretes de pendências até o vencimento',
    'integer',
    NOW(),
    NOW()
)
ON CONFLICT (chave) DO NOTHING;

-- Verifica as configurações criadas
SELECT * FROM configuracao_sistema 
WHERE chave IN ('lembretes_dias_antes_vencimento_inicio', 'lembretes_intervalo_dias')
ORDER BY chave;
