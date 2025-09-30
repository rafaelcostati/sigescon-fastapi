-- Migration: Adicionar configurações para Modelo de Relatório Global
-- Descrição: Permite que administradores façam upload de um modelo de relatório
--            que estará disponível para download em todos os contratos
-- Data: 30/09/2025
-- Versão: 2.6

-- Adicionar configurações para o modelo de relatório
INSERT INTO configuracao_sistema (chave, valor, descricao, tipo)
VALUES 
    ('modelo_relatorio_arquivo_id', NULL, 'ID do arquivo modelo de relatório no sistema de arquivos', 'integer'),
    ('modelo_relatorio_nome_original', NULL, 'Nome original do arquivo modelo de relatório', 'string'),
    ('modelo_relatorio_ativo', 'false', 'Indica se existe um modelo de relatório ativo no sistema', 'boolean')
ON CONFLICT (chave) DO NOTHING;

-- Comentários explicativos
COMMENT ON COLUMN configuracao_sistema.chave IS 'Chave única da configuração';
COMMENT ON COLUMN configuracao_sistema.valor IS 'Valor da configuração (pode ser NULL para modelo_relatorio_arquivo_id quando não há modelo)';
COMMENT ON COLUMN configuracao_sistema.descricao IS 'Descrição da configuração';
COMMENT ON COLUMN configuracao_sistema.tipo IS 'Tipo de dado da configuração (string, integer, boolean, etc)';

-- Verificar se as configurações foram criadas
SELECT chave, valor, descricao, tipo 
FROM configuracao_sistema 
WHERE chave LIKE 'modelo_relatorio%'
ORDER BY chave;
