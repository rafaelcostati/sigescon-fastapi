-- MIGRAÇÃO: Tornar perfil_id opcional na tabela usuario
-- =====================================================
-- Data: 2025-09-19
-- Objetivo: Permitir criação de usuários sem perfil_id para usar sistema de múltiplos perfis
-- =====================================================

-- IMPORTANTE: Execute este script apenas UMA VEZ!

BEGIN;

-- 1. Verificar se a migração já foi aplicada
DO $$
BEGIN
    -- Verifica se a coluna já permite NULL
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'usuario' 
        AND column_name = 'perfil_id' 
        AND is_nullable = 'NO'
    ) THEN
        RAISE NOTICE 'Aplicando migração: tornando perfil_id opcional...';
        
        -- 2. Remover a constraint NOT NULL da coluna perfil_id
        ALTER TABLE usuario ALTER COLUMN perfil_id DROP NOT NULL;
        
        RAISE NOTICE 'Migração concluída: perfil_id agora é opcional';
    ELSE
        RAISE NOTICE 'Migração já aplicada: perfil_id já é opcional';
    END IF;
END
$$;

-- 3. Adicionar comentário explicativo
COMMENT ON COLUMN usuario.perfil_id IS 'Perfil legado (opcional) - Use sistema de múltiplos perfis via tabela usuario_perfil';

-- 4. Verificar se o sistema de múltiplos perfis está ativo
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuario_perfil') THEN
        RAISE EXCEPTION 'ERRO: Tabela usuario_perfil não encontrada! Execute primeiro o script multiplo.sql';
    END IF;
    
    RAISE NOTICE 'Sistema de múltiplos perfis confirmado: tabela usuario_perfil existe';
END
$$;

COMMIT;

-- =====================================================
-- VERIFICAÇÕES PÓS-MIGRAÇÃO
-- =====================================================

-- Verificar se a migração foi bem-sucedida
SELECT 
    column_name,
    is_nullable,
    column_default,
    data_type
FROM information_schema.columns 
WHERE table_name = 'usuario' 
AND column_name = 'perfil_id';

-- Contar usuários por situação de perfil
SELECT 
    'Usuários com perfil_id preenchido' as situacao,
    COUNT(*) as quantidade
FROM usuario 
WHERE perfil_id IS NOT NULL AND ativo = TRUE

UNION ALL

SELECT 
    'Usuários sem perfil_id (novo sistema)' as situacao,
    COUNT(*) as quantidade
FROM usuario 
WHERE perfil_id IS NULL AND ativo = TRUE

UNION ALL

SELECT 
    'Total de usuários ativos' as situacao,
    COUNT(*) as quantidade
FROM usuario 
WHERE ativo = TRUE;

-- =====================================================
-- INSTRUÇÕES DE USO
-- =====================================================

/*
APÓS EXECUTAR ESTA MIGRAÇÃO:

1. Usuários podem ser criados sem perfil_id:
   INSERT INTO usuario (nome, email, cpf, senha, perfil_id) 
   VALUES ('João', 'joao@test.com', '12345678901', 'hash', NULL);

2. Perfis devem ser concedidos via sistema de múltiplos perfis:
   INSERT INTO usuario_perfil (usuario_id, perfil_id, concedido_por_usuario_id)
   VALUES (usuario_id, perfil_id, admin_id);

3. Endpoints disponíveis:
   - POST /usuarios/ (cria usuário sem perfil)
   - POST /usuarios/com-perfis (cria usuário e concede perfis)
   - POST /api/v1/usuarios/{id}/perfis/conceder (concede perfis)

4. Usuários existentes continuam funcionando normalmente
   (perfil_id preenchido + entradas na tabela usuario_perfil)
*/
