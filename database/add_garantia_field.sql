-- =====================================================
-- ADICIONAR CAMPO 'GARANTIA' NA TABELA CONTRATO
-- Sistema de Gestão de Contratos (SIGESCON)
-- =====================================================

-- Conectar ao banco de dados contratos
\c contratos;

-- Adicionar coluna garantia na tabela contrato
ALTER TABLE contrato ADD COLUMN garantia DATE;

-- Adicionar comentário para documentar o campo
COMMENT ON COLUMN contrato.garantia IS 'Data de garantia do contrato (campo opcional)';

-- Verificar se a coluna foi adicionada com sucesso
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'contrato' AND column_name = 'garantia';

ECHO 'Campo garantia adicionado com sucesso na tabela contrato!';