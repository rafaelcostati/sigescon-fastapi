-- Migration: Criação da tabela de logs de auditoria
-- Data: 2025-09-30
-- Descrição: Tabela para rastrear todas as ações importantes no sistema

-- Tabela de logs de auditoria
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,

    -- Quem fez a ação
    usuario_id INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    usuario_nome VARCHAR(255) NOT NULL,  -- Denormalizado para histórico
    perfil_usado VARCHAR(50),            -- Qual perfil estava ativo

    -- O que foi feito
    acao VARCHAR(100) NOT NULL,          -- Ex: "CRIAR", "ATUALIZAR", "DELETAR", "APROVAR", "REJEITAR"
    entidade VARCHAR(100) NOT NULL,      -- Ex: "CONTRATO", "PENDENCIA", "RELATORIO", "CONFIG"
    entidade_id INTEGER,                 -- ID da entidade afetada (NULL para ações gerais)

    -- Detalhes da ação
    descricao TEXT NOT NULL,             -- Descrição legível da ação
    dados_anteriores JSONB,              -- Estado antes da mudança (para UPDATEs)
    dados_novos JSONB,                   -- Estado depois da mudança

    -- Metadados
    ip_address VARCHAR(45),              -- IPv4 ou IPv6
    user_agent TEXT,                     -- Navegador/cliente

    -- Timestamp
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Índices
    CONSTRAINT audit_log_acao_check CHECK (acao IN (
        'CRIAR', 'ATUALIZAR', 'DELETAR', 'ATIVAR', 'DESATIVAR',
        'APROVAR', 'REJEITAR', 'ENVIAR', 'CONCLUIR', 'CANCELAR',
        'LOGIN', 'LOGOUT', 'ALTERNAR_PERFIL',
        'UPLOAD', 'DOWNLOAD', 'REMOVER_ARQUIVO',
        'CRIAR_PENDENCIAS_AUTOMATICAS', 'ATUALIZAR_CONFIG'
    ))
);

-- Índices para melhorar performance de consultas
CREATE INDEX idx_audit_log_usuario_id ON audit_log(usuario_id);
CREATE INDEX idx_audit_log_entidade ON audit_log(entidade, entidade_id);
CREATE INDEX idx_audit_log_acao ON audit_log(acao);
CREATE INDEX idx_audit_log_data_hora ON audit_log(data_hora DESC);
CREATE INDEX idx_audit_log_perfil ON audit_log(perfil_usado);

-- Comentários
COMMENT ON TABLE audit_log IS 'Tabela de auditoria para rastrear todas as ações no sistema';
COMMENT ON COLUMN audit_log.usuario_id IS 'ID do usuário que realizou a ação';
COMMENT ON COLUMN audit_log.usuario_nome IS 'Nome do usuário (denormalizado para histórico)';
COMMENT ON COLUMN audit_log.perfil_usado IS 'Perfil ativo no momento da ação';
COMMENT ON COLUMN audit_log.acao IS 'Tipo de ação realizada';
COMMENT ON COLUMN audit_log.entidade IS 'Tipo de entidade afetada';
COMMENT ON COLUMN audit_log.entidade_id IS 'ID da entidade afetada';
COMMENT ON COLUMN audit_log.descricao IS 'Descrição legível da ação';
COMMENT ON COLUMN audit_log.dados_anteriores IS 'Estado anterior (JSON)';
COMMENT ON COLUMN audit_log.dados_novos IS 'Estado novo (JSON)';
COMMENT ON COLUMN audit_log.ip_address IS 'Endereço IP do cliente';
COMMENT ON COLUMN audit_log.user_agent IS 'User agent do navegador';
COMMENT ON COLUMN audit_log.data_hora IS 'Data e hora da ação';

-- Função para limpar logs antigos (opcional - executar manualmente ou via cron)
CREATE OR REPLACE FUNCTION limpar_audit_logs_antigos(dias_retencao INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    registros_deletados INTEGER;
BEGIN
    DELETE FROM audit_log
    WHERE data_hora < CURRENT_TIMESTAMP - (dias_retencao || ' days')::INTERVAL;

    GET DIAGNOSTICS registros_deletados = ROW_COUNT;
    RETURN registros_deletados;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION limpar_audit_logs_antigos IS 'Remove logs de auditoria mais antigos que X dias (padrão: 365)';
