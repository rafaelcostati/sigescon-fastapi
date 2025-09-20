-- SIGESCON - Script SQL para reset completo do banco
-- ATENÇÃO: Este script APAGA TODOS OS DADOS!

-- ============================================================================
-- LIMPEZA COMPLETA (desabilita FKs temporariamente)
-- ============================================================================

SET session_replication_role = 'replica';

TRUNCATE TABLE "relatoriofiscal" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "pendenciarelatorio" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "arquivo" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "contrato" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "contratado" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "usuario" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "statusrelatorio" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "statuspendencia" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "status" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "modalidade" RESTART IDENTITY CASCADE;
TRUNCATE TABLE "perfil" RESTART IDENTITY CASCADE;

SET session_replication_role = 'origin';

-- ============================================================================
-- DADOS ESSENCIAIS
-- ============================================================================

-- Perfis de usuário
INSERT INTO "perfil" (nome) VALUES
('Administrador'),
('Gestor'),
('Fiscal');

-- Modalidades de contrato
INSERT INTO "modalidade" (nome) VALUES
('Pregão Eletrônico'),
('Pregão Presencial'),
('Concorrência'),
('Concurso'),
('Leilão'),
('Diálogo Competitivo'),
('Dispensa de Licitação'),
('Inexigibilidade de Licitação'),
('Credenciamento');

-- Status de contratos
INSERT INTO "status" (nome) VALUES
('Vigente'),
('Encerrado'),
('Rescindido'),
('Suspenso'),
('Aguardando Publicação'),
('Em Execução'),
('Finalizado');

-- Status de relatórios
INSERT INTO "statusrelatorio" (nome) VALUES
('Pendente de Análise'),
('Aprovado'),
('Rejeitado com Pendência');

-- Status de pendências
INSERT INTO "statuspendencia" (nome) VALUES
('Pendente'),
('Concluída'),
('Cancelada');

-- ============================================================================
-- USUÁRIOS PADRÃO
-- ============================================================================

-- Admin (senha: admin123)
INSERT INTO "usuario" (nome, email, cpf, matricula, senha, perfil_id) VALUES
('Administrador do Sistema', 'admin@sigescon.gov.br', '00000000000', 'ADM001',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.A6MvM6aB2', 1);

-- Gestor (senha: gestor123)
INSERT INTO "usuario" (nome, email, cpf, matricula, senha, perfil_id) VALUES
('João Silva - Gestor', 'gestor@sigescon.gov.br', '11111111111', 'GES001',
 '$2b$12$5hn9fN0qQlJX6Q4E7JY8eeQZGj8TQYnUzp0vBczn5WQkEwE0HCp3K', 2);

-- Fiscal (senha: fiscal123)
INSERT INTO "usuario" (nome, email, cpf, matricula, senha, perfil_id) VALUES
('Maria Santos - Fiscal', 'fiscal@sigescon.gov.br', '22222222222', 'FIS001',
 '$2b$12$IkF6THkGQ0YnEL8xZVV0.OrOhAC8YqY9jEK0JwU.mKJ2qN3YgY0LG', 3);

-- ============================================================================
-- DADOS DE EXEMPLO
-- ============================================================================

-- Empresas/pessoas contratadas
INSERT INTO "contratado" (nome, cnpj, telefone, email) VALUES
('Tech Solutions Ltda', '12345678000199', '11999887766', 'contato@techsolutions.com.br'),
('Construtora ABC S.A.', '98765432000188', '11888776655', 'obras@construtorabc.com.br');

INSERT INTO "contratado" (nome, cpf, telefone, email) VALUES
('João Consultor MEI', '33333333333', '11777665544', 'joao.consultor@email.com');

-- Contratos de exemplo
INSERT INTO "contrato" (numero, objeto, descricao, data_assinatura, data_inicio, data_fim, valor, contratado_id, modalidade_id, status_id, gestor_id, fiscal_id) VALUES
('CONT/2024/001',
 'Desenvolvimento de Sistema de Gestão de Contratos',
 'Desenvolvimento completo de sistema web para gestão de contratos governamentais incluindo módulos de usuários, contratos, relatórios e pendências.',
 '2024-01-15', '2024-02-01', '2024-12-31', 250000.00,
 1, 1, 6, 2, 3),

('CONT/2024/002',
 'Reforma do Prédio Administrativo',
 'Reforma completa do prédio administrativo incluindo pintura, elétrica, hidráulica e climatização.',
 '2024-03-10', '2024-04-01', '2024-08-30', 180000.00,
 2, 3, 1, 2, 3),

('CONT/2024/003',
 'Consultoria em Gestão de Processos',
 'Consultoria especializada para mapeamento e otimização de processos administrativos.',
 '2024-02-20', '2024-03-01', '2024-06-30', 45000.00,
 3, 7, 7, 2, 3);

-- Pendências de exemplo
INSERT INTO "pendenciarelatorio" (descricao, data_prazo, status_pendencia_id, contrato_id, criado_por_usuario_id) VALUES
('Enviar relatório mensal de acompanhamento - Janeiro/2024', '2024-02-10', 1, 1, 1),
('Relatório de execução física e financeira - 1º Trimestre', '2024-04-15', 1, 2, 1);

-- ============================================================================
-- VERIFICAÇÃO FINAL
-- ============================================================================

SELECT 'DADOS INSERIDOS:' as status;
SELECT 'Perfis' as tabela, COUNT(*) as total FROM "perfil"
UNION ALL
SELECT 'Usuários', COUNT(*) FROM "usuario"
UNION ALL
SELECT 'Modalidades', COUNT(*) FROM "modalidade"
UNION ALL
SELECT 'Status', COUNT(*) FROM "status"
UNION ALL
SELECT 'Contratados', COUNT(*) FROM "contratado"
UNION ALL
SELECT 'Contratos', COUNT(*) FROM "contrato"
UNION ALL
SELECT 'Pendências', COUNT(*) FROM "pendenciarelatorio";

SELECT '✅ BANCO RESETADO E POPULADO COM SUCESSO!' as resultado;