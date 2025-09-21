# 🚀 SETUP DO SISTEMA SIGESCON

Este documento explica como usar o novo script unificado `setup_sistema.sh` que substitui os scripts antigos.

## 📋 Scripts Substituídos

O `setup_sistema.sh` **substitui completamente** os seguintes scripts:
- ❌ `reset_clean.sh`
- ❌ `reset_database.sh`
- ❌ `reset_examples.sh`

## 🎯 Opções Disponíveis

### 1️⃣ **Setup Básico**
Insere apenas os dados **essenciais** para funcionamento do sistema:

#### 📊 Dados Inseridos:
- **Perfis**: Administrador, Gestor, Fiscal
- **Status Contrato**: Ativo, Suspenso, Encerrado, Cancelado
- **Status Pendência**: Pendente, Concluída, Cancelada, Aguardando Análise
- **Status Relatório**: Pendente de Análise, Aprovado, Rejeitado com Pendência
- **Modalidades**: Pregão Eletrônico, Concorrência, etc.
- **Usuário Admin**: Configurado conforme `.env`

#### 🎯 Ideal para:
- Ambiente de produção
- Início limpo do sistema
- Quando não precisa de dados de exemplo

---

### 2️⃣ **Setup com Dados de Teste**
Inclui **tudo do Setup Básico** + dados completos para demonstração:

#### 📊 Dados Adicionais:
- **👥 Usuários de Teste:**
  - João Silva Fiscal (`joao.fiscal@sigescon.gov.br`)
  - Maria Santos Fiscal (`maria.fiscal@sigescon.gov.br`)
  - Carlos Gestor Silva (`carlos.gestor@sigescon.gov.br`)
  - Senha para todos: `Fiscal@123` / `Gestor@123`

- **🏢 Contratados de Exemplo:**
  - Empresa ABC Ltda
  - Tecnologia XYZ S.A.
  - Serviços DEF Eireli

- **📋 Contratos Completos:**
  - PGE-001/2025: Desenvolvimento de software
  - PGE-002/2025: Equipamentos de informática
  - PGE-003/2025: Manutenção predial

- **📝 Pendências em Todos os Status:**
  - **Vencidas**: Data 20/08/2025 (para testar alertas)
  - **Futuras**: 15 dias após hoje
  - **Aguardando Análise**: Com relatórios já enviados
  - **Concluídas**: Finalizadas com sucesso

#### 🎯 Ideal para:
- Desenvolvimento e testes
- Demonstrações do sistema
- Treinamento de usuários
- Validação de funcionalidades

---

## 🚀 Como Usar

### Execução Interativa:
```bash
./setup_sistema.sh
```

O script apresentará um menu amigável para escolher a opção desejada.

### Verificações Automáticas:
- ✅ Ambiente virtual ativo
- ✅ Arquivo `.env` configurado
- ✅ Diretório correto
- ✅ Dependências instaladas

### Segurança:
- ⚠️ Sempre solicita confirmação antes de apagar dados
- 📋 Mostra configurações antes de executar
- 🔄 Operação atômica (tudo ou nada)

---

## 📊 Estrutura de Dados

### Status do Sistema (IDs fixos):

#### Status de Contrato:
| ID | Nome      | Descrição           |
|----|-----------|---------------------|
| 1  | Ativo     | Contrato vigente    |
| 2  | Suspenso  | Temporariamente parado |
| 3  | Encerrado | Finalizado normalmente |
| 4  | Cancelado | Cancelado/rescindido |

#### Status de Pendência:
| ID | Nome                | Descrição                    |
|----|---------------------|------------------------------|
| 1  | Pendente           | Aguardando ação do fiscal    |
| 2  | Concluída          | Relatório aprovado           |
| 3  | Cancelada          | Cancelada pelo admin         |
| 4  | Aguardando Análise | Relatório enviado, aguardando análise |

#### Status de Relatório:
| ID | Nome                        | Descrição                |
|----|-----------------------------|--------------------------|
| 1  | Pendente de Análise         | Aguardando análise       |
| 2  | Aprovado                    | Aprovado pelo admin      |
| 3  | Rejeitado com Pendência     | Rejeitado, deve corrigir |

---

## 🔧 Configuração Necessária

### Arquivo `.env` deve conter:
```env
# Banco de dados
DATABASE_URL="postgresql://user:password@host:port/database"

# Usuário administrador
ADMIN_EMAIL="admin@sigescon.gov.br"
ADMIN_PASSWORD="Admin@123"

# Outras configurações...
JWT_SECRET_KEY="sua_chave_secreta"
```

---

## 🎯 Casos de Uso

### 🏭 **Produção**:
```bash
./setup_sistema.sh
# Escolher opção 1 (Setup Básico)
```

### 🧪 **Desenvolvimento/Testes**:
```bash
./setup_sistema.sh
# Escolher opção 2 (Setup com Dados de Teste)
```

### 🎓 **Treinamento**:
```bash
./setup_sistema.sh
# Escolher opção 2 (Setup com Dados de Teste)
# Usuários podem fazer login e explorar todas as funcionalidades
```

---

## ⚡ Performance

- **Setup Básico**: ~5 segundos
- **Setup Completo**: ~15 segundos
- **Operação Atômica**: Rollback automático em caso de erro
- **Sincronização**: Sequências do banco ajustadas automaticamente

---

## 🔄 Migração dos Scripts Antigos

Se você ainda tem os scripts antigos, pode removê-los:

```bash
# Opcional: remover scripts antigos
rm -f reset_clean.sh reset_database.sh reset_examples.sh

# O novo script substitui todos eles
./setup_sistema.sh
```

---

## 🛡️ Segurança

- ⚠️ **SEMPRE** faz backup antes de usar em produção
- 🔒 Senhas são hasheadas com bcrypt
- 🎲 CPFs/CNPJs de teste são gerados aleatoriamente
- 🔐 Confirmação obrigatória antes de apagar dados

---

## 📞 Suporte

Em caso de problemas:
1. Verifique se o `.env` está configurado corretamente
2. Confirme que o banco de dados está acessível
3. Execute com ambiente virtual ativo
4. Verifique logs para detalhes de erro

---

**🎉 Agora você tem um sistema de setup unificado, poderoso e fácil de usar!**