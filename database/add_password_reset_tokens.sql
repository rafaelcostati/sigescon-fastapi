-- =====================================================
-- ADICIONAR TABELA DE TOKENS DE RESET DE SENHA
-- Sistema de Gestão de Contratos (SIGESCON)
-- =====================================================

-- Conectar ao banco contratos
\c contratos;

-- =====================================================
-- TABELA: password_reset_tokens
-- =====================================================
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(255) NOT NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance e segurança
CREATE UNIQUE INDEX idx_unique_password_reset_token ON password_reset_tokens (token);
CREATE INDEX idx_password_reset_tokens_usuario_id ON password_reset_tokens (usuario_id);
CREATE INDEX idx_password_reset_tokens_expires_at ON password_reset_tokens (expires_at);

-- Trigger para updated_at
CREATE TRIGGER update_password_reset_tokens_updated_at
    BEFORE UPDATE ON password_reset_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentário da tabela
COMMENT ON TABLE password_reset_tokens IS 'Tokens para reset de senha dos usuários';
COMMENT ON COLUMN password_reset_tokens.token IS 'Token único para reset de senha';
COMMENT ON COLUMN password_reset_tokens.usuario_id IS 'Referência ao usuário que solicitou o reset';
COMMENT ON COLUMN password_reset_tokens.expires_at IS 'Data de expiração do token (24 horas)';
COMMENT ON COLUMN password_reset_tokens.used_at IS 'Data de uso do token (NULL se não usado)';
111
-- Exibir confirmação
SELECT 'Tabela password_reset_tokens criada com sucesso!' as resultado;

-- Verificar estrutura da tabela
\d password_reset_tokens;