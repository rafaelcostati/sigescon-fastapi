# 🗄️ Reset e Seed do Banco de Dados SIGESCON

Scripts para limpar completamente o banco de dados e recriar com dados essenciais para desenvolvimento e testes.

## ⚠️ **ATENÇÃO**
**Estes scripts APAGAM TODOS OS DADOS do banco de dados!**
Use apenas em ambientes de desenvolvimento ou quando precisar resetar completamente o sistema.

---

## 🚀 Opções de Execução

### 1. **Script Python Completo (Recomendado)**
```bash
cd /caminho/para/sigescon-fastapi
python scripts/reset_and_seed_database.py
```

**Características:**
- ✅ Interativo com confirmação de segurança
- ✅ Verificações de integridade
- ✅ Logs detalhados do processo
- ✅ Tratamento de erros robusto
- ✅ Dados realistas para desenvolvimento

### 2. **Script Shell (Linux/Mac)**
```bash
cd /caminho/para/sigescon-fastapi
./reset_database.sh
```

**Características:**
- ✅ Verifica ambiente virtual automaticamente
- ✅ Carrega variáveis do arquivo .env
- ✅ Interface amigável
- ✅ Executa o script Python internamente

### 3. **Script SQL Direto**
```bash
psql -U postgres -d contratos -f scripts/reset_database.sql
```

**Características:**
- ⚡ Execução mais rápida
- 🔧 Pode ser usado em qualquer cliente SQL
- ⚠️ Senhas pré-definidas (usar apenas em desenvolvimento)

### 4. **Reset Rápido (Sem Confirmação)**
```bash
python scripts/quick_reset.py
```

**Características:**
- ⚡ Para automação/CI/CD
- 🚫 Sem confirmação interativa
- 🔄 Execução silenciosa

---

## 📊 Dados Criados

### 👥 **Usuários Padrão**
| Perfil | Email | Senha | Descrição |
|--------|-------|--------|-----------|
| **Administrador** | admin@sigescon.gov.br | admin123 | Acesso total ao sistema |
| **Gestor** | gestor@sigescon.gov.br | gestor123 | Gestão de contratos e equipes |
| **Fiscal** | fiscal@sigescon.gov.br | fiscal123 | Fiscalização e relatórios |

### 🏢 **Empresas/Pessoas Contratadas**
- **Tech Solutions Ltda** - Empresa de tecnologia
- **Construtora ABC S.A.** - Empresa de construção
- **João Consultor MEI** - Consultor pessoa física

### 📄 **Contratos de Exemplo**
- **CONT/2024/001** - Desenvolvimento de Sistema (250k)
- **CONT/2024/002** - Reforma de Prédio (180k)
- **CONT/2024/003** - Consultoria (45k)

### 📋 **Dados de Lookup**
- **Perfis**: Administrador, Gestor, Fiscal
- **Modalidades**: Pregão, Concorrência, Dispensa, etc.
- **Status**: Vigente, Encerrado, Suspenso, etc.
- **Status de Relatórios**: Pendente, Aprovado, Rejeitado
- **Status de Pendências**: Pendente, Concluída, Cancelada

### ⚠️ **Pendências Criadas**
- Relatório mensal de Janeiro/2024
- Relatório trimestral do 1º trimestre

---

## 🔧 Configuração

### **Variáveis de Ambiente (.env)**
```env
# Banco de dados
DATABASE_URL="postgresql://postgres:senha@localhost:5432/contratos"

# OU configuração individual:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=contratos
DB_USER=postgres
DB_PASSWORD=senha

# Usuário administrador
ADMIN_EMAIL=admin@sigescon.gov.br
ADMIN_PASSWORD=admin123

# Configurações JWT
JWT_SECRET_KEY=sua_chave_secreta_muito_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### **Pré-requisitos**
1. **PostgreSQL** rodando e acessível
2. **Banco `contratos`** criado (pode estar vazio)
3. **Ambiente virtual** Python ativo
4. **Dependências** instaladas: `pip install -e .`

---

## 🔄 Casos de Uso

### **Desenvolvimento Local**
```bash
# Setup inicial do projeto
./reset_database.sh

# Acesse o sistema
# http://localhost:8000/docs
# Login: admin@sigescon.gov.br / admin123
```

### **Testes Automatizados**
```bash
# Reset antes dos testes
python scripts/quick_reset.py

# Execute os testes
pytest -v
```

### **Demonstração/Homologação**
```bash
# Reset com dados limpos
python scripts/reset_and_seed_database.py

# Sistema pronto para demonstração
# Dados realistas mas fictícios
```

---

## 🚨 Troubleshooting

### **Erro: "relation does not exist"**
```bash
# Recrie as tabelas primeiro
psql -U postgres -d contratos -f database/database.sql

# Depois execute o reset
./reset_database.sh
```

### **Erro: "permission denied"**
```bash
# Torne o script executável
chmod +x reset_database.sh

# OU execute diretamente com Python
python scripts/reset_and_seed_database.py
```

### **Erro: "connection refused"**
```bash
# Verifique se PostgreSQL está rodando
sudo systemctl status postgresql

# Verifique as configurações de conexão
echo $DATABASE_URL
```

### **Erro: "ModuleNotFoundError"**
```bash
# Certifique-se de estar no diretório correto
cd /caminho/para/sigescon-fastapi

# E que o ambiente virtual está ativo
source .venv/bin/activate

# Instale as dependências
pip install -e .
```

---

## 📝 Logs e Monitoramento

### **Logs de Execução**
O script Python exibe logs detalhados:
```
🔄 LIMPANDO BANCO DE DADOS
✅ Tabela 'perfil' limpa
✅ Tabela 'usuario' limpa
...

🔄 POPULANDO TABELAS DE LOOKUP
✅ Tabela 'perfil': 3 registros inseridos
...

📊 Registros criados:
   • perfil: 3 registros
   • usuario: 3 registros
   • contrato: 3 registros
   ...
```

### **Verificação Pós-Reset**
```sql
-- Conte os registros criados
SELECT
    'perfil' as tabela, COUNT(*) as total FROM perfil
UNION ALL
SELECT 'usuario', COUNT(*) FROM usuario
UNION ALL
SELECT 'contrato', COUNT(*) FROM contrato;

-- Teste de login
SELECT nome, email FROM usuario WHERE ativo = true;
```

---

## 🔒 Segurança

### **⚠️ Senhas Padrão**
As senhas padrão são **apenas para desenvolvimento**:
- `admin123`, `gestor123`, `fiscal123`

### **🔐 Produção**
Para produção:
1. **Mude as senhas** imediatamente após o primeiro login
2. **Configure variáveis** de ambiente seguras
3. **Use HTTPS** sempre
4. **Implemente** políticas de senha fortes

### **🗃️ Backup**
Sempre faça backup antes de executar:
```bash
# Backup completo
pg_dump -U postgres contratos > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore se necessário
psql -U postgres -d contratos < backup_20241201_143022.sql
```

---

## 📋 Checklist de Execução

### **Antes de Executar**
- [ ] Backup do banco atual (se necessário)
- [ ] Variáveis de ambiente configuradas
- [ ] PostgreSQL rodando
- [ ] Ambiente virtual ativo
- [ ] Dependências instaladas

### **Execução**
- [ ] Script executado sem erros
- [ ] Logs verificados
- [ ] Contagem de registros confirmada

### **Verificação**
- [ ] Login funcionando (admin@sigescon.gov.br)
- [ ] API respondendo (/health)
- [ ] Documentação acessível (/docs)
- [ ] Dados de exemplo visíveis

---

**✅ Com estes scripts, o banco estará sempre limpo e pronto para desenvolvimento!**