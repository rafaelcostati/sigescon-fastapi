# 🔧 Correção do Race Condition entre Workers Gunicorn

## 📋 Problema Identificado

O sistema estava apresentando comportamento inconsistente na troca de perfis em produção:
- **Localmente**: Funcionava perfeitamente
- **Produção**: Funcionava esporadicamente ("Uma hora deu certo e alterou, depois não deu certo")

### 🔍 Causa Raiz
**Race condition entre workers do Gunicorn**: O estado da sessão estava sendo armazenado em uma variável global (`_GLOBAL_ACTIVE_PROFILES`) que não é compartilhada entre diferentes processos worker.

**Logs evidenciaram o problema:**
- Worker 69579: ✅ Sucesso na troca de perfil
- Worker 69576: ❌ Erro 403 - sessão não encontrada

## ✅ Solução Implementada

### 1. **Persistência em Banco de Dados**
- Substituída a variável global pela tabela `session_context` existente
- Todas as operações de sessão agora usam PostgreSQL como fonte única da verdade

### 2. **Métodos Atualizados**
- `create_session_context()` - Cria sessão no banco
- `get_session_context()` - Busca sessão no banco com validação de expiração
- `update_active_profile()` - Atualiza perfil no banco com validação
- `get_active_session_by_user()` - Busca sessão ativa mais recente
- `deactivate_session()` - Desativa sessão no banco
- `cleanup_expired_sessions()` - Remove sessões expiradas

### 3. **Remoção Completa do Estado Global**
- Eliminada dependência de `_GLOBAL_ACTIVE_PROFILES`
- Removido código de fallback emergency
- Limpeza de debug logs excessivos

## 🧪 Como Testar

### 1. **Teste Local**
```bash
# 1. Aplicar as mudanças
git pull

# 2. Reiniciar o servidor
uvicorn app.main:app --reload --port 8000

# 3. Testar troca de perfil no frontend
# - Login com usuário multi-perfil
# - Alternar perfis várias vezes
# - Verificar consistência
```

### 2. **Teste em Produção**
```bash
# 1. Deploy das mudanças
# 2. Reiniciar workers Gunicorn
sudo systemctl restart gunicorn

# 3. Teste com múltiplos usuários simultaneamente
# - Múltiplas abas/dispositivos
# - Trocas de perfil consecutivas
# - Verificar logs para confirmar sucesso
```

### 3. **Verificação de Logs**
```bash
# Logs esperados:
✅ DEBUG: Sessão encontrada no banco - usuario X, perfil Y
✅ DEBUG: Perfil atualizado no banco - sessao Z, novo perfil W

# Não devem aparecer mais:
❌ ERROR: Contexto não encontrado! Criando contexto de emergência...
🆘 EMERGENCY: [qualquer log de emergency]
```

## 📊 Estrutura da Tabela `session_context`

```sql
CREATE TABLE session_context (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    perfil_ativo_id INTEGER NOT NULL REFERENCES perfil(id),
    sessao_id VARCHAR(255) NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_expiracao TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE
);
```

## 🎯 Benefícios da Solução

### ✅ **Antes vs Depois**

| Aspecto | Antes (Global State) | Depois (Database) |
|---------|---------------------|-------------------|
| **Consistência** | Inconsistente entre workers | ✅ Sempre consistente |
| **Escalabilidade** | Limitada a 1 worker | ✅ Múltiplos workers |
| **Persistência** | Perdida no restart | ✅ Persiste entre restarts |
| **Debugging** | Difícil rastreamento | ✅ Logs claros e rastreáveis |
| **Performance** | Memória limitada | ✅ Escalável com banco |

### 🚀 **Características Técnicas**
- **Thread-Safe**: Operações atômicas no PostgreSQL
- **Worker-Independent**: Cada worker acessa a mesma fonte de dados
- **Auto-Cleanup**: Sessões expiradas são automaticamente limpas
- **Backwards Compatible**: Mantém API existente intacta

## 🔧 Arquivos Modificados

1. **`app/repositories/session_context_repo.py`**
   - Implementação completa de persistência em banco
   - Remoção total do estado global
   - Métodos robustos com tratamento de erro

2. **`app/api/routers/auth_router.py`**
   - Remoção do código de fallback emergency
   - Tratamento de erro mais limpo
   - Logs de debug otimizados

## 🎉 Resultado Esperado

**O sistema agora deve funcionar de forma 100% consistente em produção, independentemente de:**
- Número de workers Gunicorn
- Load balancing entre workers
- Restarts do servidor
- Múltiplos usuários simultâneos

**O comportamento será idêntico ao ambiente local, eliminando a intermitência reportada.**