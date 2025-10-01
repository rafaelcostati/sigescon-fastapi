-- Migration: Adicionar configurações para Alertas de Vencimento de Contratos
-- Descrição: Permite configurar alertas automáticos de contratos vencendo
--            com seleção de perfis destinatários e periodicidade customizada
-- Data: 30/09/2025
-- Versão: 2.7

-- Adicionar configurações para alertas de vencimento de contratos
INSERT INTO configuracao_sistema (chave, valor, descricao, tipo)
VALUES 
    -- Habilitar/desabilitar alertas
    ('alertas_vencimento_ativo', 'true', 'Indica se os alertas de vencimento de contratos estão ativos', 'boolean'),
    
    -- Dias antes do vencimento para começar alertas
    ('alertas_vencimento_dias_antes', '90', 'Quantos dias antes do vencimento começar a enviar alertas (1-365)', 'integer'),
    
    -- Periodicidade de reenvio em dias
    ('alertas_vencimento_periodicidade_dias', '30', 'A cada quantos dias reenviar o alerta (1-90)', 'integer'),
    
    -- Perfis que receberão os alertas (JSON array)
    ('alertas_vencimento_perfis_destino', '["Administrador"]', 'Perfis que receberão os alertas: Administrador, Gestor, Fiscal', 'json'),
    
    -- Hora do dia para enviar (formato HH:MM)
    ('alertas_vencimento_hora_envio', '10:00', 'Hora do dia para enviar os alertas (formato HH:MM)', 'string')
ON CONFLICT (chave) DO NOTHING;

-- Comentários explicativos
COMMENT ON COLUMN configuracao_sistema.chave IS 'Chave única da configuração';
COMMENT ON COLUMN configuracao_sistema.valor IS 'Valor da configuração';
COMMENT ON COLUMN configuracao_sistema.descricao IS 'Descrição da configuração';
COMMENT ON COLUMN configuracao_sistema.tipo IS 'Tipo de dado da configuração (string, integer, boolean, json, etc)';

-- Verificar se as configurações foram criadas
SELECT chave, valor, descricao, tipo 
FROM configuracao_sistema 
WHERE chave LIKE 'alertas_vencimento%'
ORDER BY chave;

-- =====================================================
-- EXEMPLOS DE USO:
-- =====================================================

-- Exemplo 1: Alertas para Gestores, 90 dias antes, a cada 30 dias
-- UPDATE configuracao_sistema SET valor = '90' WHERE chave = 'alertas_vencimento_dias_antes';
-- UPDATE configuracao_sistema SET valor = '30' WHERE chave = 'alertas_vencimento_periodicidade_dias';
-- UPDATE configuracao_sistema SET valor = '["Gestor"]' WHERE chave = 'alertas_vencimento_perfis_destino';

-- Exemplo 2: Alertas para Gestores E Fiscais, 60 dias antes, a cada 15 dias
-- UPDATE configuracao_sistema SET valor = '60' WHERE chave = 'alertas_vencimento_dias_antes';
-- UPDATE configuracao_sistema SET valor = '15' WHERE chave = 'alertas_vencimento_periodicidade_dias';
-- UPDATE configuracao_sistema SET valor = '["Gestor", "Fiscal"]' WHERE chave = 'alertas_vencimento_perfis_destino';

-- Exemplo 3: Alertas para Administradores (relatório completo), 120 dias antes, a cada 45 dias
-- UPDATE configuracao_sistema SET valor = '120' WHERE chave = 'alertas_vencimento_dias_antes';
-- UPDATE configuracao_sistema SET valor = '45' WHERE chave = 'alertas_vencimento_periodicidade_dias';
-- UPDATE configuracao_sistema SET valor = '["Administrador"]' WHERE chave = 'alertas_vencimento_perfis_destino';

-- Exemplo 4: Alertas para todos os perfis
-- UPDATE configuracao_sistema SET valor = '["Administrador", "Gestor", "Fiscal"]' WHERE chave = 'alertas_vencimento_perfis_destino';

-- =====================================================
-- LÓGICA DE FUNCIONAMENTO:
-- =====================================================
-- 
-- 1. Sistema verifica diariamente contratos próximos do vencimento
-- 2. Se faltarem <= 'alertas_vencimento_dias_antes' dias:
--    - Envia primeiro alerta
--    - Registra data do último envio
-- 3. Reenvia alerta a cada 'alertas_vencimento_periodicidade_dias' dias
-- 4. Destinatários baseados em 'alertas_vencimento_perfis_destino':
--    - Administrador: Recebe relatório consolidado de TODOS os contratos vencendo
--    - Gestor: Recebe apenas dos contratos que gerencia
--    - Fiscal: Recebe apenas dos contratos que fiscaliza
-- 5. Envia no horário configurado em 'alertas_vencimento_hora_envio'
