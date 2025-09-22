-- =====================================================
-- SCRIPT COMPLETO DE CRIAÇÃO DO BANCO DE DADOS
-- Sistema de Gestão de Contratos (SIGESCON)
-- =====================================================

-- Remover banco se existir e criar novo
DROP DATABASE IF EXISTS contratos;
CREATE DATABASE contratos;
\c contratos;

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABELA: perfil
-- =====================================================
CREATE TABLE perfil (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice único para nome ativo
CREATE UNIQUE INDEX idx_unique_perfil_nome_ativo ON perfil (nome) WHERE (ativo IS TRUE);

-- =====================================================
-- TABELA: usuario
-- =====================================================
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    matricula VARCHAR(50),
    cpf VARCHAR(14),
    senha_hash VARCHAR(255) NOT NULL,
    perfil_id INTEGER REFERENCES perfil(id),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices únicos para campos ativos
CREATE UNIQUE INDEX idx_unique_usuario_email_ativo ON usuario (email) WHERE (ativo IS TRUE);
CREATE UNIQUE INDEX idx_unique_usuario_cpf_ativo ON usuario (cpf) WHERE (ativo IS TRUE);
CREATE UNIQUE INDEX idx_unique_usuario_matricula_ativo ON usuario (matricula) WHERE (ativo IS TRUE);

-- =====================================================
-- TABELA: usuario_perfil (relacionamento N:N)
-- =====================================================
CREATE TABLE usuario_perfil (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    perfil_id INTEGER NOT NULL REFERENCES perfil(id),
    concedido_por_usuario_id INTEGER REFERENCES usuario(id),
    data_concessao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance e unicidade
CREATE INDEX idx_usuario_perfil_usuario_id ON usuario_perfil (usuario_id) WHERE (ativo IS TRUE);
CREATE INDEX idx_usuario_perfil_perfil_id ON usuario_perfil (perfil_id) WHERE (ativo IS TRUE);
CREATE UNIQUE INDEX usuario_perfil_usuario_id_perfil_id_key ON usuario_perfil (usuario_id, perfil_id) WHERE (ativo IS TRUE);

-- =====================================================
-- TABELA: session_context
-- =====================================================
CREATE TABLE session_context (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    perfil_ativo_id INTEGER NOT NULL REFERENCES perfil(id),
    sessao_id VARCHAR(255) NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_expiracao TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE
);

-- Índices para performance
CREATE INDEX idx_session_context_usuario_id ON session_context (usuario_id) WHERE (ativo IS TRUE);
CREATE INDEX idx_session_context_sessao_id ON session_context (sessao_id) WHERE (ativo IS TRUE);
CREATE UNIQUE INDEX session_context_sessao_id_key ON session_context (sessao_id);

-- =====================================================
-- TABELA: modalidade
-- =====================================================
CREATE TABLE modalidade (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice único para nome ativo
CREATE UNIQUE INDEX idx_unique_modalidade_nome_ativo ON modalidade (nome) WHERE (ativo IS TRUE);

-- =====================================================
-- TABELA: status
-- =====================================================
CREATE TABLE status (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice único para nome ativo
CREATE UNIQUE INDEX idx_unique_status_nome_ativo ON status (nome) WHERE (ativo IS TRUE);

-- =====================================================
-- TABELA: contratado
-- =====================================================
CREATE TABLE contratado (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18),
    cpf VARCHAR(14),
    email VARCHAR(255),
    telefone VARCHAR(20),
    endereco TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices únicos para campos ativos
CREATE UNIQUE INDEX idx_unique_contratado_cnpj_ativo ON contratado (cnpj) WHERE (ativo IS TRUE AND cnpj IS NOT NULL);
CREATE UNIQUE INDEX idx_unique_contratado_cpf_ativo ON contratado (cpf) WHERE (ativo IS TRUE AND cpf IS NOT NULL);
CREATE UNIQUE INDEX idx_unique_contratado_email_ativo ON contratado (email) WHERE (ativo IS TRUE AND email IS NOT NULL);

-- =====================================================
-- TABELA: contrato
-- =====================================================
CREATE TABLE contrato (
    id SERIAL PRIMARY KEY,
    nr_contrato VARCHAR(50) NOT NULL,
    objeto TEXT NOT NULL,
    valor_anual DECIMAL(15,2),
    valor_global DECIMAL(15,2),
    base_legal TEXT,
    data_inicio DATE,
    data_fim DATE,
    termos_contratuais TEXT,
    contratado_id INTEGER NOT NULL REFERENCES contratado(id),
    modalidade_id INTEGER NOT NULL REFERENCES modalidade(id),
    status_id INTEGER NOT NULL REFERENCES status(id),
    gestor_id INTEGER NOT NULL REFERENCES usuario(id),
    fiscal_id INTEGER NOT NULL REFERENCES usuario(id),
    fiscal_substituto_id INTEGER REFERENCES usuario(id),
    pae TEXT,
    doe TEXT,
    data_doe DATE,
    documento TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE UNIQUE INDEX idx_unique_contrato_nr_contrato_ativo ON contrato (nr_contrato) WHERE (ativo IS TRUE);
CREATE INDEX idx_contrato_contratado_id ON contrato (contratado_id);
CREATE INDEX idx_contrato_modalidade_id ON contrato (modalidade_id);
CREATE INDEX idx_contrato_status_id ON contrato (status_id);
CREATE INDEX idx_contrato_gestor_id ON contrato (gestor_id);
CREATE INDEX idx_contrato_fiscal_id ON contrato (fiscal_id);
CREATE INDEX idx_contrato_data_fim ON contrato (data_fim);

-- =====================================================
-- TABELA: statuspendencia
-- =====================================================
CREATE TABLE statuspendencia (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice único para nome ativo
CREATE UNIQUE INDEX idx_unique_statuspendencia_nome_ativo ON statuspendencia (nome) WHERE (ativo IS TRUE);

-- =====================================================
-- TABELA: pendenciarelatorio
-- =====================================================
CREATE TABLE pendenciarelatorio (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL REFERENCES contrato(id),
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    data_prazo DATE NOT NULL,
    status_pendencia_id INTEGER NOT NULL REFERENCES statuspendencia(id),
    criado_por_usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_pendenciarelatorio_contrato_id ON pendenciarelatorio (contrato_id);
CREATE INDEX idx_pendenciarelatorio_data_prazo ON pendenciarelatorio (data_prazo);

-- =====================================================
-- TABELA: statusrelatorio
-- =====================================================
CREATE TABLE statusrelatorio (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice único para nome ativo
CREATE UNIQUE INDEX idx_unique_statusrelatorio_nome_ativo ON statusrelatorio (nome) WHERE (ativo IS TRUE);

-- =====================================================
-- TABELA: arquivo
-- =====================================================
CREATE TABLE arquivo (
    id SERIAL PRIMARY KEY,
    nome_arquivo VARCHAR(255) NOT NULL,
    caminho_arquivo TEXT NOT NULL,
    tamanho_bytes BIGINT,
    tipo_mime VARCHAR(100),
    contrato_id INTEGER REFERENCES contrato(id),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABELA: relatoriofiscal
-- =====================================================
CREATE TABLE relatoriofiscal (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL REFERENCES contrato(id),
    pendencia_id INTEGER REFERENCES pendenciarelatorio(id),
    titulo VARCHAR(255),
    descricao TEXT,
    observacoes TEXT,
    fiscal_usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    aprovador_usuario_id INTEGER REFERENCES usuario(id),
    arquivo_id INTEGER REFERENCES arquivo(id),
    status_id INTEGER NOT NULL REFERENCES statusrelatorio(id),
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_analise TIMESTAMP,
    observacoes_analise TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_relatoriofiscal_contrato_id ON relatoriofiscal (contrato_id);
CREATE UNIQUE INDEX relatoriofiscal_arquivo_id_key ON relatoriofiscal (arquivo_id) WHERE (arquivo_id IS NOT NULL);

-- =====================================================
-- VIEW: v_usuario_perfis
-- =====================================================
CREATE VIEW v_usuario_perfis AS
SELECT 
    u.id AS usuario_id,
    u.nome AS usuario_nome,
    u.email AS usuario_email,
    u.matricula AS usuario_matricula,
    p.id AS perfil_id,
    p.nome AS perfil_nome,
    up.data_concessao,
    up.ativo AS perfil_ativo
FROM usuario u
INNER JOIN usuario_perfil up ON u.id = up.usuario_id
INNER JOIN perfil p ON up.perfil_id = p.id
WHERE u.ativo = TRUE AND up.ativo = TRUE AND p.ativo = TRUE;

-- =====================================================
-- TRIGGERS PARA UPDATED_AT
-- =====================================================

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger em todas as tabelas
CREATE TRIGGER update_perfil_updated_at BEFORE UPDATE ON perfil FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_usuario_updated_at BEFORE UPDATE ON usuario FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_usuario_perfil_updated_at BEFORE UPDATE ON usuario_perfil FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_modalidade_updated_at BEFORE UPDATE ON modalidade FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_status_updated_at BEFORE UPDATE ON status FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contratado_updated_at BEFORE UPDATE ON contratado FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contrato_updated_at BEFORE UPDATE ON contrato FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_statuspendencia_updated_at BEFORE UPDATE ON statuspendencia FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pendenciarelatorio_updated_at BEFORE UPDATE ON pendenciarelatorio FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_statusrelatorio_updated_at BEFORE UPDATE ON statusrelatorio FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_arquivo_updated_at BEFORE UPDATE ON arquivo FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_relatoriofiscal_updated_at BEFORE UPDATE ON relatoriofiscal FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- COMENTÁRIOS DAS TABELAS
-- =====================================================

COMMENT ON TABLE perfil IS 'Perfis de acesso do sistema (Administrador, Gestor, Fiscal)';
COMMENT ON TABLE usuario IS 'Usuários do sistema';
COMMENT ON TABLE usuario_perfil IS 'Relacionamento N:N entre usuários e perfis';
COMMENT ON TABLE session_context IS 'Contexto de sessão dos usuários logados';
COMMENT ON TABLE modalidade IS 'Modalidades de contratação';
COMMENT ON TABLE status IS 'Status dos contratos';
COMMENT ON TABLE contratado IS 'Empresas/pessoas contratadas';
COMMENT ON TABLE contrato IS 'Contratos do sistema';
COMMENT ON TABLE statuspendencia IS 'Status das pendências de relatórios';
COMMENT ON TABLE pendenciarelatorio IS 'Pendências de relatórios fiscais';
COMMENT ON TABLE statusrelatorio IS 'Status dos relatórios fiscais';
COMMENT ON TABLE arquivo IS 'Arquivos anexados aos contratos e relatórios';
COMMENT ON TABLE relatoriofiscal IS 'Relatórios fiscais enviados';

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================

-- Exibir resumo das tabelas criadas
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

ECHO 'Base de dados criada com sucesso!';
