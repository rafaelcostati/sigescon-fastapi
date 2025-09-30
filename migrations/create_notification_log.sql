-- Migration: Criar tabela notification_log para controlar envio de alertas
-- Data: 2025-09-30
-- Descrição: Tabela para evitar envio duplicado de alertas de contratos e garantias

CREATE TABLE IF NOT EXISTS notification_log (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,  -- 'contract_expiration' ou 'garantia_expiration'
    contrato_id INTEGER NOT NULL REFERENCES contrato(id) ON DELETE CASCADE,
    alert_milestone INTEGER NOT NULL,  -- 90, 60 ou 30 (dias)
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índice único para evitar duplicatas: mesmo contrato + tipo + marco
    CONSTRAINT unique_notification UNIQUE (notification_type, contrato_id, alert_milestone)
);

-- Índices para performance
CREATE INDEX idx_notification_log_contrato_id ON notification_log(contrato_id);
CREATE INDEX idx_notification_log_type ON notification_log(notification_type);
CREATE INDEX idx_notification_log_sent_at ON notification_log(sent_at);

-- Comentários
COMMENT ON TABLE notification_log IS 'Registra alertas enviados para contratos e garantias';
COMMENT ON COLUMN notification_log.notification_type IS 'Tipo: contract_expiration ou garantia_expiration';
COMMENT ON COLUMN notification_log.alert_milestone IS 'Marco de dias: 90, 60 ou 30';