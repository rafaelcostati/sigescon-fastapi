# 🚀 CLAUDE.md - SIGESCON FastAPI

## 📖 Visão Geral do Projeto

O **SIGESCON** (Sistema de Gestão de Contratos) é uma API robusta desenvolvida em **FastAPI** para gerenciamento completo do ciclo de vida de contratos governamentais. O projeto está em **produção** e oferece funcionalidades avançadas de gestão, fiscalização e relatórios.

### 🎯 Objetivo Principal
Sistema completo para gerenciar contratos, usuários, fiscalizações e relatórios com fluxo de aprovação, notificações automáticas e sistema de auditoria.

---

## 🏗️ Arquitetura do Sistema

### Estrutura em Camadas (Clean Architecture)
```
┌─────────────────┐
│   API Routes    │  ← FastAPI endpoints com validação Pydantic
├─────────────────┤
│   Middlewares   │  ← Auditoria, CORS, timing, exception handling
├─────────────────┤
│    Services     │  ← Lógica de negócio e orquestração
├─────────────────┤
│  Repositories   │  ← Acesso a dados com queries otimizadas (AsyncPG)
├─────────────────┤
│    Database     │  ← PostgreSQL 14+ com connection pooling
└─────────────────┘
```

### Padrões Implementados
- **Repository Pattern** - Isolamento da camada de dados
- **Service Layer** - Centralização da lógica de negócio
- **Dependency Injection** - Injeção de dependências nativa do FastAPI
- **DTO Pattern** - Schemas Pydantic para validação
- **Async/Await** - Operações assíncronas em toda aplicação
- **Middleware Pattern** - Cross-cutting concerns

---

## 📁 Estrutura de Diretórios

```
backend-contratos-FASTAPI/
├── app/
│   ├── main.py                      # Aplicação principal FastAPI
│   ├── seeder.py                    # Popular dados iniciais
│   │
│   ├── api/                         # Camada de API
│   │   ├── dependencies.py          # Injeção de dependências
│   │   ├── permissions.py           # Controle de permissões
│   │   ├── doc_dependencies.py      # Proteção da documentação
│   │   ├── exception_handlers.py    # Tratamento global de exceções
│   │   └── routers/                 # Endpoints REST
│   │       ├── auth_router.py       # Autenticação e contexto
│   │       ├── usuario_router.py    # CRUD de usuários
│   │       ├── contrato_router.py   # Gestão de contratos
│   │       ├── contratado_router.py # Empresas/pessoas contratadas
│   │       ├── pendencia_router.py  # Pendências de relatórios
│   │       ├── relatorio_router.py  # Relatórios fiscais
│   │       ├── arquivo_router.py    # Download de arquivos
│   │       └── [tabelas_aux]_router.py
│   │
│   ├── core/                        # Configurações centrais
│   │   ├── config.py                # Settings e env vars
│   │   ├── database.py              # Pool de conexões PostgreSQL
│   │   ├── security.py              # JWT, hashing, autenticação
│   │   └── exceptions.py            # Exceções customizadas
│   │
│   ├── middleware/                  # Middlewares customizados
│   │   ├── audit.py                 # Auditoria de ações
│   │   └── logging.py               # Configuração de logs
│   │
│   ├── repositories/                # Camada de dados (AsyncPG)
│   │   ├── usuario_repo.py          # Queries de usuários
│   │   ├── contrato_repo.py         # Queries de contratos
│   │   ├── contratado_repo.py       # Queries de contratados
│   │   └── [outros]_repo.py
│   │
│   ├── schemas/                     # Modelos Pydantic
│   │   ├── usuario_schema.py        # DTOs de usuários
│   │   ├── contrato_schema.py       # DTOs de contratos
│   │   ├── session_context_schema.py # Contexto de sessão
│   │   └── [outros]_schema.py
│   │
│   └── services/                    # Lógica de negócio
│       ├── usuario_service.py       # Negócio de usuários
│       ├── contrato_service.py      # Negócio de contratos
│       ├── email_service.py         # Envio de emails
│       ├── file_service.py          # Gerenciamento de arquivos
│       └── notification_service.py  # Scheduler de notificações
│
├── database/
│   └── database.sql                 # Script completo do banco
│
├── tests/                           # Testes automatizados
│   ├── conftest.py                  # Configuração dos testes
│   ├── test_auth_e_usuarios.py      # Testes de autenticação
│   ├── test_usuarios_complete.py    # Testes completos de usuários
│   ├── test_contratados.py          # Testes de contratados
│   └── fixtures/                    # Arquivos de teste
│
├── uploads/                         # Arquivos enviados
├── logs/                            # Logs da aplicação
├── scripts/                         # Scripts auxiliares
├── .env                            # Variáveis de ambiente
├── pyproject.toml                  # Configuração do projeto
├── pytest.ini                     # Configuração de testes
├── run_tests.sh                    # Script de validação
└── README.md                       # Documentação completa
```

---

## 🛠️ Stack Tecnológica

### Backend Core
- **FastAPI** 0.100+ - Framework web assíncrono
- **Python** 3.10+ - Linguagem principal
- **Pydantic** - Validação de dados e serialização
- **AsyncPG** - Driver PostgreSQL assíncrono

### Banco de Dados
- **PostgreSQL** 14+ - Banco relacional principal
- **Connection Pooling** - Pool otimizado de conexões
- **Soft Delete** - Preservação de histórico

### Autenticação & Segurança
- **python-jose** - JWT com criptografia
- **passlib + bcrypt** - Hashing seguro de senhas
- **CORS** - Cross-origin resource sharing

### Funcionalidades Avançadas
- **aiofiles** - Manipulação assíncrona de arquivos
- **aiosmtplib** - Envio assíncrono de emails
- **APScheduler** - Tarefas agendadas e lembretes

### Testing & Development
- **pytest** + **pytest-asyncio** - Framework de testes
- **httpx** - Cliente HTTP para testes
- **uvicorn** - Servidor ASGI

---

## 🚀 Como Executar

### 1. Configuração Inicial
```bash
# Clone e entre no diretório
cd backend-contratos-FASTAPI

# Ative o ambiente virtual
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instale dependências
pip install -e .
```

### 2. Configuração do Banco
```bash
# PostgreSQL deve estar rodando
# Banco: contratos
# Usuário/senha conforme .env

# Execute o script de criação
psql -U postgres -d contratos -f database/database.sql
```

### 3. Variáveis de Ambiente (.env)
```env
DATABASE_URL="postgresql://postgres:senha@localhost:5432/contratos"
JWT_SECRET_KEY=sua_chave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_EMAIL=admin@sigescon.com
ADMIN_PASSWORD=senha_admin
SMTP_SERVER=smtp.servidor.com
SMTP_PORT=587
SENDER_EMAIL=email@dominio.com
SENDER_PASSWORD=senha_email
```

### 4. Executar Aplicação
```bash
# Desenvolvimento (com hot reload)
uvicorn app.main:app --reload --port 8000

# Produção
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### 5. Executar Testes
```bash
# Todos os testes
pytest -v --asyncio-mode=auto

# Com cobertura
pytest --cov=app tests/

# Script completo de validação
chmod +x run_tests.sh
./run_tests.sh
```

---

## 🔑 Funcionalidades Principais

### Sistema de Autenticação
- **JWT Tokens** - Autenticação segura com expiração
- **Múltiplos Perfis** - Usuário pode ter vários papéis (Admin, Gestor, Fiscal)
- **Contexto de Sessão** - Alternância entre perfis sem logout
- **Permissões Granulares** - Controle de acesso por perfil

### Gestão de Usuários
- **CRUD Completo** - Criar, listar, atualizar, deletar
- **Validações** - CPF, email, senhas fortes
- **Gestão de Perfis** - Concessão/revogação de papéis
- **Alteração de Senhas** - Própria e administrativa

### Gestão de Contratos
- **Upload de Arquivos** - Documentos contratuais
- **Associações** - Gestores, fiscais, substitutos
- **Filtros Avançados** - Por data, status, responsáveis
- **Soft Delete** - Preservação de histórico

### Relatórios Fiscais
- **Workflow Completo** - Submissão → Análise → Aprovação/Rejeição
- **Upload de Documentos** - Relatórios com anexos
- **Histórico de Versões** - Controle de reenvios
- **Feedback** - Comentários em caso de rejeição

### Pendências
- **Criação Automática** - Tarefas para fiscais
- **Controle de Prazos** - Notificações em intervalos
- **Status de Conclusão** - Acompanhamento do progresso

### Notificações
- **Emails Automáticos** - SMTP assíncrono
- **Scheduler** - APScheduler para lembretes
- **Templates** - Emails personalizados por tipo

---

## 🔌 API Endpoints

### Autenticação
```
POST   /auth/login                    # Login com email/senha
POST   /auth/alternar-perfil          # Alternar perfil ativo
GET    /auth/contexto                 # Contexto atual da sessão
GET    /auth/dashboard                # Dados para dashboard
GET    /auth/permissoes               # Permissões do usuário
```

### Usuários
```
GET    /api/v1/usuarios               # Listar usuários (paginado)
POST   /api/v1/usuarios               # Criar usuário (Admin)
GET    /api/v1/usuarios/{id}          # Buscar usuário específico
PATCH  /api/v1/usuarios/{id}          # Atualizar usuário
DELETE /api/v1/usuarios/{id}          # Deletar usuário (soft)
GET    /api/v1/usuarios/me            # Dados do usuário logado
PATCH  /api/v1/usuarios/{id}/alterar-senha    # Alterar própria senha
PATCH  /api/v1/usuarios/{id}/resetar-senha    # Reset senha (Admin)
```

### Perfis de Usuário
```
GET    /api/v1/usuarios/{id}/perfis           # Listar perfis do usuário
POST   /api/v1/usuarios/{id}/perfis/conceder  # Conceder perfis
POST   /api/v1/usuarios/{id}/perfis/revogar   # Revogar perfis
```

### Contratos
```
GET    /api/v1/contratos              # Listar contratos (filtros)
POST   /api/v1/contratos              # Criar contrato + upload
GET    /api/v1/contratos/{id}         # Detalhes do contrato
PATCH  /api/v1/contratos/{id}         # Atualizar contrato
DELETE /api/v1/contratos/{id}         # Deletar contrato
```

### Relatórios e Pendências
```
GET    /api/v1/contratos/{id}/relatorios     # Listar relatórios
POST   /api/v1/contratos/{id}/relatorios     # Submeter relatório
PATCH  /api/v1/contratos/{id}/relatorios/{id}/analise  # Analisar

GET    /api/v1/contratos/{id}/pendencias     # Listar pendências
POST   /api/v1/contratos/{id}/pendencias     # Criar pendência
```

### Arquivos e Tabelas Auxiliares
```
GET    /api/v1/arquivos/{id}/download        # Download seguro
GET    /api/v1/contratados                   # Empresas/pessoas
GET    /api/v1/perfis                        # Tipos de perfil
GET    /api/v1/modalidades                   # Modalidades de contrato
GET    /api/v1/status                        # Status possíveis
```

### Monitoramento
```
GET    /                              # Info da API
GET    /health                        # Health check
GET    /metrics                       # Métricas básicas
GET    /docs                          # Swagger UI (protegido)
GET    /redoc                         # ReDoc (protegido)
```

---

## 🧪 Testes

### Estrutura de Testes
```bash
tests/
├── conftest.py                    # Fixtures globais
├── test_auth_e_usuarios.py        # Auth e CRUD usuários
├── test_usuarios_complete.py      # Testes completos
├── test_contratados.py            # Entidade contratados
└── fixtures/                      # Arquivos de teste
    ├── contrato_teste.pdf
    └── relatorio_teste.txt
```

### Executar Testes
```bash
# Todos os testes
pytest -sv --asyncio-mode=auto

# Módulo específico
pytest tests/test_usuarios_complete.py -v

# Com cobertura
pytest --cov=app tests/

# Script completo (inclui validação de servidor)
./run_tests.sh
```

### Fixtures Principais
- **db_pool** - Pool de conexões para testes
- **admin_user** - Usuário administrador
- **auth_headers** - Headers com token JWT
- **sample_contrato** - Dados de contrato para testes

---

## 🔒 Sistema de Permissões

### Perfis de Usuário
| Perfil | Permissões |
|--------|------------|
| **Administrador** | Acesso total - CRUD usuários, contratos, aprovar relatórios |
| **Gestor** | Visualizar contratos sob gestão, analisar relatórios da equipe |
| **Fiscal** | Submeter relatórios, visualizar pendências designadas |

### Contexto de Sessão
- Usuário pode ter **múltiplos perfis** simultaneamente
- **Alternância de contexto** sem necessidade de logout
- Permissões **dinâmicas** baseadas no perfil ativo
- **Token JWT** inclui informações do contexto atual

### Decoradores de Permissão
```python
@admin_required          # Apenas administradores
@fiscal_required         # Fiscais e superiores
@gestor_required         # Gestores e superiores
@owner_or_admin          # Próprio usuário ou admin
```

---

## 📧 Sistema de Notificações

### Configuração SMTP
```python
# Configuração no .env
SMTP_SERVER=mail.servidor.com
SMTP_PORT=587
SENDER_EMAIL=sistema@dominio.com
SENDER_PASSWORD=senha_app
```

### Tipos de Notificação
- **Pendência Criada** - Fiscal recebe nova tarefa
- **Relatório Submetido** - Admin notificado para análise
- **Relatório Aprovado** - Fiscal informado da aprovação
- **Relatório Rejeitado** - Fiscal recebe feedback para correção
- **Lembrete de Prazo** - Alertas automáticos por cronograma

### Scheduler de Lembretes
```python
# APScheduler configurado em notification_service.py
# Executa verificações periódicas
# Envia lembretes baseados em prazos
# Configurável por tipo de pendência
```

---

## 🔍 Middleware e Auditoria

### Middleware de Auditoria
```python
# app/middleware/audit.py
# Registra todas as ações críticas:
# - Criação/alteração de usuários
# - Submissão de relatórios
# - Aprovação/rejeição
# - Login/logout
# - Mudanças de permissão
```

### Middleware de Timing
```python
# Headers de resposta:
X-Process-Time: 0.123        # Tempo de processamento
X-Request-ID: a1b2c3d4       # ID único para rastreamento
```

### Tratamento de Exceções
```python
# Exception handlers globais:
# - SigesconException (regras de negócio)
# - DatabaseException (erros de BD)
# - ValidationException (dados inválidos)
# - HTTPException (erros HTTP)
# - GenericException (fallback)
```

---

## 🚀 Deploy e Produção

### Comandos de Produção
```bash
# Com Uvicorn
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# Com Gunicorn + Uvicorn Workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Monitoramento
```bash
# Health check
curl http://localhost:8000/health

# Métricas
curl http://localhost:8000/metrics
```

---

## 📚 Documentação da API

### Swagger UI
- **URL**: http://localhost:8000/docs
- **Proteção**: Requer login de administrador
- **Funcionalidades**: Interface interativa completa

### ReDoc
- **URL**: http://localhost:8000/redoc
- **Proteção**: Requer login de administrador
- **Funcionalidades**: Documentação clean e responsiva

### OpenAPI Schema
- **URL**: http://localhost:8000/openapi.json
- **Formato**: JSON Schema OpenAPI 3.0
- **Uso**: Geração de clientes SDK

---

## 🔧 Comandos Úteis para Claude

### Desenvolvimento
```bash
# Instalar dependências
pip install -e .

# Executar testes específicos
pytest tests/test_usuarios_complete.py::TestUsuariosCRUD::test_criar_usuario -v

# Executar servidor de desenvolvimento
uvicorn app.main:app --reload --port 8000

# Verificar sintaxe e tipos
python -m py_compile app/main.py
mypy app/ --ignore-missing-imports
```

### Debugging
```bash
# Logs da aplicação
tail -f logs/app.log

# Verificar conexão com banco
psql "postgresql://postgres:senha@localhost:5432/contratos" -c "SELECT version();"

# Testar endpoint específico
curl -X GET "http://localhost:8000/health" -H "accept: application/json"
```

### Banco de Dados
```bash
# Conectar ao banco
psql -U postgres -d contratos

# Verificar tabelas
\dt

# Ver usuários cadastrados
SELECT id, nome, email, data_criacao FROM usuarios WHERE data_exclusao IS NULL;

# Ver contratos ativos
SELECT numero, objeto, data_assinatura FROM contratos WHERE data_exclusao IS NULL;
```

---

## 🎯 Status da Migração (Flask → FastAPI)

### ✅ Concluído
- [x] **Sistema de Usuários** - CRUD completo com testes
- [x] **Autenticação JWT** - Login e contexto de sessão
- [x] **Múltiplos Perfis** - Concessão/revogação dinâmica
- [x] **Contratados** - CRUD com validações
- [x] **Tabelas Auxiliares** - Perfis, Status, Modalidades
- [x] **Contratos** - Gestão completa com upload
- [x] **Relatórios e Pendências** - Workflow implementado
- [x] **Sistema de Emails** - SMTP assíncrono
- [x] **Scheduler** - Notificações automáticas
- [x] **Middleware** - Auditoria e logging
- [x] **Testes** - Cobertura abrangente
- [x] **Documentação** - Swagger protegido

### 🚀 Em Produção
O sistema está **100% funcional** e em **produção ativa**, oferecendo todas as funcionalidades do sistema Flask original com melhorias significativas em performance e manutenibilidade.

---

## 📞 Suporte e Contato

### Documentação
- **Swagger**: http://localhost:8000/docs (requer admin)
- **ReDoc**: http://localhost:8000/redoc (requer admin)
- **README**: Documentação completa no README.md

### Monitoramento
- **Health Check**: http://localhost:8000/health
- **Métricas**: http://localhost:8000/metrics
- **Logs**: Diretório `logs/`

### Desenvolvimento
- **Testes**: `pytest -v --asyncio-mode=auto`
- **Validação**: `./run_tests.sh`
- **Hot Reload**: `uvicorn app.main:app --reload`

---

*Este é um sistema em produção com arquitetura robusta, testes abrangentes e documentação completa. Pronto para manutenção, extensão e evolução contínua.*