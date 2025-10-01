-- Migration: Sistema de Escalonamento de Pendências
-- Data: 2025-09-30
-- Descrição: Configurações para notificar gestor e admin quando pendências não são resolvidas

-- Adicionar configurações de escalonamento na tabela configuracao_sistema
INSERT INTO configuracao_sistema (chave, valor, descricao, tipo) VALUES
(
    'escalonamento_gestor_dias',
    '7',
    'Dias após vencimento da pendência para notificar o gestor',
    'integer'
),
(
    'escalonamento_admin_dias',
    '14',
    'Dias após vencimento da pendência para notificar o administrador',
    'integer'
),
(
    'escalonamento_ativo',
    'true',
    'Ativar ou desativar o sistema de escalonamento',
    'boolean'
)
ON CONFLICT (chave) DO UPDATE SET
    valor = EXCLUDED.valor,
    descricao = EXCLUDED.descricao,
    tipo = EXCLUDED.tipo;

-- Comentários
COMMENT ON TABLE configuracao_sistema IS 'Tabela de configurações do sistema, incluindo escalonamento de pendências';

-- Verificar se as configurações foram inseridas
SELECT chave, valor, descricao FROM configuracao_sistema WHERE chave LIKE 'escalonamento%';
