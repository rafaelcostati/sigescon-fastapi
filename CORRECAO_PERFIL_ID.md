# 🔧 CORREÇÃO URGENTE: perfil_id NOT NULL

## Problema Identificado

O erro que você encontrou acontece porque a coluna `perfil_id` na tabela `usuario` está definida como `NOT NULL`, mas o novo sistema de múltiplos perfis precisa criar usuários sem perfil inicial.

```
null value in column "perfil_id" of relation "usuario" violates not-null constraint
```

## Solução Rápida

Execute **UM** dos comandos abaixo para corrigir:

### Opção 1: Script Python (Recomendado)
```bash
cd /home/rafael/backend-contratos-FASTAPI
python scripts/fix_perfil_id_quick.py
```

### Opção 2: SQL Direto no PostgreSQL
```sql
-- Conecte ao banco sigescon e execute:
ALTER TABLE usuario ALTER COLUMN perfil_id DROP NOT NULL;
```

### Opção 3: Script Completo de Migração
```bash
cd /home/rafael/backend-contratos-FASTAPI
python scripts/executar_migracao_perfil_id.py
```

## Verificação

Após executar a correção, verifique se funcionou:

```sql
-- Deve retornar 'YES' para is_nullable
SELECT is_nullable 
FROM information_schema.columns 
WHERE table_name = 'usuario' AND column_name = 'perfil_id';
```

## Teste da Correção

Após aplicar a correção, **reinicie o servidor** e teste novamente:

```bash
# Reiniciar servidor
# Depois testar via /docs:
POST /usuarios/
{
  "nome": "Teste Usuario",
  "email": "teste@example.com",
  "cpf": "12345678901",
  "matricula": "TEST001",
  "senha": "senha123"
}
```

## Fluxo Completo Após Correção

1. **Criar usuário** (sem perfil):
   ```bash
   POST /usuarios/
   ```

2. **Conceder perfis**:
   ```bash
   POST /api/v1/usuarios/{user_id}/perfis/conceder
   {
     "perfil_ids": [2, 3],
     "observacoes": "Perfis Fiscal e Gestor"
   }
   ```

3. **OU usar endpoint conveniente**:
   ```bash
   POST /usuarios/com-perfis
   {
     "user": { ... dados do usuário ... },
     "perfil_ids": [2, 3]
   }
   ```

## Arquivos Criados

- ✅ `database/migration_perfil_id_nullable.sql` - Migração completa
- ✅ `scripts/executar_migracao_perfil_id.py` - Script Python completo  
- ✅ `scripts/fix_perfil_id_quick.py` - Correção rápida
- ✅ `docs/exemplo_criacao_usuario_multiplos_perfis.md` - Documentação de uso

## Status da Implementação

- ✅ Schema atualizado (`UsuarioCreate.perfil_id` opcional)
- ✅ Repository ajustado (sempre cria com `perfil_id = NULL`)
- ✅ Router com novos endpoints
- ✅ Documentação completa
- ⚠️  **PENDENTE**: Executar migração no banco de dados

## Próximos Passos

1. **Execute a correção** (uma das opções acima)
2. **Reinicie o servidor**
3. **Teste a criação de usuários**
4. **Use o sistema de múltiplos perfis**

---

**IMPORTANTE**: Esta correção é **segura** e **não afeta usuários existentes**. Apenas permite criar novos usuários sem perfil_id inicial.
