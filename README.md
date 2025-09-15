# 🚀 SIGESCON API - Sistema de Gestão de Contratos

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Sistema robusto de gestão de contratos desenvolvido com **FastAPI**, oferecendo uma API RESTful completa para gerenciamento do ciclo de vida de contratos, relatórios fiscais e fluxos de aprovação.

## 📑 Índice

- [🚀 SIGESCON API - Sistema de Gestão de Contratos](#-sigescon-api---sistema-de-gestão-de-contratos)
  - [📑 Índice](#-índice)
  - [✨ Características](#-características)
    - [Core Features](#core-features)
    - [Módulos Principais](#módulos-principais)
      - [👤 **Usuários**](#-usuários)
      - [📋 **Contratos**](#-contratos)
      - [📝 **Relatórios Fiscais**](#-relatórios-fiscais)
      - [⏰ **Pendências**](#-pendências)
  - [🏗 Arquitetura](#-arquitetura)
    - [Padrões Implementados](#padrões-implementados)
  - [🛠 Tecnologias](#-tecnologias)
    - [Backend](#backend)
    - [Database](#database)
    - [Testing](#testing)
  - [📋 Pré-requisitos](#-pré-requisitos)
  - [🚀 Instalação](#-instalação)
    - [1. Clone o repositório](#1-clone-o-repositório)
    - [2. Crie um ambiente virtual](#2-crie-um-ambiente-virtual)
    - [3. Instale as dependências](#3-instale-as-dependências)
    - [4. Configure o banco de dados](#4-configure-o-banco-de-dados)
  - [⚙️ Configuração](#️-configuração)
    - [1. Crie o arquivo .env na raiz do projeto](#1-crie-o-arquivo-env-na-raiz-do-projeto)
    - [2. Execute o seeder para dados iniciais](#2-execute-o-seeder-para-dados-iniciais)
  - [🏃 Execução](#-execução)
    - [Modo Desenvolvimento](#modo-desenvolvimento)
    - [Modo Produção](#modo-produção)
    - [Scheduler (Lembretes automáticos)](#scheduler-lembretes-automáticos)
  - [🧪 Testes](#-testes)
    - [Executar todos os testes](#executar-todos-os-testes)
    - [Script de validação completo](#script-de-validação-completo)
  - [📖 API Documentation](#-api-documentation)
    - [Endpoints Principais](#endpoints-principais)
      - [Autenticação](#autenticação)
      - [Usuários](#usuários)
      - [Contratos](#contratos)
      - [Relatórios](#relatórios)
      - [Pendências](#pendências)
      - [Tabelas Auxiliares](#tabelas-auxiliares)
  - [📁 Estrutura do Projeto](#-estrutura-do-projeto)
  - [🔄 Fluxo de Trabalho](#-fluxo-de-trabalho)
    - [Fluxo de Relatórios Fiscais](#fluxo-de-relatórios-fiscais)
    - [Níveis de Acesso](#níveis-de-acesso)
  - [💻 Desenvolvimento](#-desenvolvimento)
    - [Convenções de Código](#convenções-de-código)
    - [Comandos Úteis](#comandos-úteis)
    - [Variáveis de Ambiente para Desenvolvimento](#variáveis-de-ambiente-para-desenvolvimento)
  - [🚢 Deploy](#-deploy)
    - [Docker](#docker)
    - [Docker Compose](#docker-compose)
    - [Heroku](#heroku)
    - [Gunicorn com Uvicorn Workers](#gunicorn-com-uvicorn-workers)
  - [🤝 Contribuindo](#-contribuindo)
    - [Guidelines](#guidelines)
  - [📄 Licença](#-licença)
  - [👥 Autores](#-autores)
  - [🙏 Agradecimentos](#-agradecimentos)
  - [📞 Suporte](#-suporte)
  - [🔗 Links Úteis](#-links-úteis)

## ✨ Características

### Core Features
- 🔐 **Autenticação JWT** - Sistema seguro de autenticação com tokens
- 👥 **Sistema de Perfis** - Três níveis de acesso (Administrador, Gestor, Fiscal)
- 📄 **Gestão de Contratos** - CRUD completo com validações e soft delete
- 📎 **Upload de Arquivos** - Suporte para múltiplos formatos com validação
- 📊 **Relatórios Fiscais** - Fluxo completo de submissão e aprovação
- 📅 **Pendências e Prazos** - Sistema de notificações e lembretes
- 📧 **Notificações por Email** - Integração com SMTP para alertas automáticos
- 📈 **Paginação e Filtros** - Busca avançada em todos os módulos
- 🔄 **Soft Delete** - Preservação do histórico de dados
- ⚡ **100% Assíncrono** - Alta performance com asyncio

### Módulos Principais

#### 👤 **Usuários**
- Criação e gestão de usuários
- Alteração e reset de senha
- Perfis com diferentes permissões

#### 📋 **Contratos**
- Cadastro completo com múltiplos campos
- Upload de documentos
- Associação com gestores e fiscais
- Filtros avançados e paginação

#### 📝 **Relatórios Fiscais**
- Submissão por fiscais
- Análise e aprovação por administradores
- Reenvio em caso de rejeição
- Histórico completo

#### ⏰ **Pendências**
- Criação de tarefas para fiscais
- Controle de prazos
- Notificações automáticas
- Status de conclusão

## 🏗 Arquitetura

O projeto segue uma arquitetura em camadas (Clean Architecture):

```
┌─────────────────┐
│   API Routes    │  ← FastAPI endpoints
├─────────────────┤
│    Services     │  ← Lógica de negócio
├─────────────────┤
│  Repositories   │  ← Acesso a dados
├─────────────────┤
│    Database     │  ← PostgreSQL + asyncpg
└─────────────────┘
```

### Padrões Implementados
- **Repository Pattern** - Isolamento da camada de dados
- **Service Layer** - Centralização da lógica de negócio
- **Dependency Injection** - Injeção de dependências nativa do FastAPI
- **DTO Pattern** - Schemas Pydantic para validação
- **Async/Await** - Operações assíncronas em toda a aplicação

## 🛠 Tecnologias

### Backend
- **FastAPI** - Framework web moderno e rápido
- **Pydantic** - Validação de dados e serialização
- **asyncpg** - Driver PostgreSQL assíncrono
- **python-jose** - Implementação JWT
- **passlib + bcrypt** - Hashing seguro de senhas
- **aiofiles** - Manipulação assíncrona de arquivos
- **aiosmtplib** - Envio assíncrono de emails
- **APScheduler** - Agendamento de tarefas

### Database
- **PostgreSQL 14+** - Banco de dados relacional
- **Migrations** - Scripts SQL versionados

### Testing
- **pytest** - Framework de testes
- **pytest-asyncio** - Suporte para testes assíncronos
- **httpx** - Cliente HTTP assíncrono para testes

## 📋 Pré-requisitos

- Python 3.10 ou superior
- PostgreSQL 14 ou superior
- pip ou uv (gerenciador de pacotes)
- Git

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/rafaelcostati/sigescon-fastapi.git
cd sigescon-fastapi
```

### 2. Crie um ambiente virtual
```bash
# Com venv
python -m venv .venv

# Ative o ambiente
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 3. Instale as dependências
```bash
# Com pip
pip install -e .

# Ou com uv (mais rápido)
uv pip install -e .
```

### 4. Configure o banco de dados
```bash
# Acesse o PostgreSQL
psql -U postgres

# Crie o banco de dados
CREATE DATABASE sigescon;
\q

# Execute o script de criação das tabelas
psql -U postgres -d sigescon -f database/database.sql
```
## ⚙️ Configuração

### 1. Crie o arquivo .env na raiz do projeto
```env
# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/sigescon

# JWT
JWT_SECRET_KEY=sua_chave_secreta_muito_segura_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720

# Admin padrão (criado pelo seeder)
ADMIN_EMAIL=admin@sigescon.com
ADMIN_PASSWORD=Admin@123

# Email (Opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=seu_email@gmail.com
SENDER_PASSWORD=sua_senha_app

# Testes (Opcional)
BASE_URL=http://localhost:8000
PDF_CONTRATO_PATH=tests/fixtures/contrato_teste.pdf
TXT_RELATORIO_PATH=tests/fixtures/relatorio_teste.txt
EMAIL_GESTOR=gestor.teste@example.com
EMAIL_FISCAL=fiscal.teste@example.com
```

### 2. Execute o seeder para dados iniciais
```bash
# Criar dados essenciais (perfis, status, etc.)
python -c "
import asyncio
import asyncpg
from app.seeder import seed_data
from app.core.config import settings

async def run_seeder():
    conn = await asyncpg.connect(settings.DATABASE_URL)
    await seed_data(conn)
    await conn.close()

asyncio.run(run_seeder())
"
```

## 🏃 Execução
### Modo Desenvolvimento
```bash
# Com uvicorn (hot reload automático)
uvicorn app.main:app --reload --port 8000

# Com configurações customizadas
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```
### Modo Produção
```bash
# Com workers para alta performance
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```
### Scheduler (Lembretes automáticos)
```bash
# Em um terminal separado
python app/scheduler.py
```
## 🧪 Testes
### Executar todos os testes
```bash
# Testes básicos
pytest -sv --asyncio-mode=auto

# Com cobertura
pytest --cov=app tests/

# Testes específicos
pytest tests/test_contratos.py -v

# Com output detalhado
pytest -v -s
```
### Script de validação completo
```bash
# Torna o script executável
chmod +x run_tests.sh

# Executa validação completa
./run_tests.sh
```
## 📖 API Documentation
Com o servidor rodando, acesse:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Endpoints Principais
#### Autenticação
- `POST /auth/login` - Login e obtenção de token

#### Usuários
- `GET /usuarios` - Listar usuários (Admin)
- `POST /usuarios` - Criar usuário (Admin)
- `GET /usuarios/{id}` - Buscar usuário
- `PATCH /usuarios/{id}` - Atualizar usuário (Admin)
- `DELETE /usuarios/{id}` - Deletar usuário (Admin)
- `GET /usuarios/me` - Dados do usuário logado
- `PATCH /usuarios/{id}/alterar-senha` - Alterar própria senha
- `PATCH /usuarios/{id}/resetar-senha` - Reset de senha (Admin)

#### Contratos
- `GET /contratos` - Listar contratos com filtros e paginação
- `POST /contratos` - Criar contrato com upload (Admin)
- `GET /contratos/{id}` - Detalhes do contrato
- `PATCH /contratos/{id}` - Atualizar contrato (Admin)
- `DELETE /contratos/{id}` - Deletar contrato (Admin)

#### Relatórios
- `GET /contratos/{id}/relatorios` - Listar relatórios
- `POST /contratos/{id}/relatorios` - Submeter relatório (Fiscal)
- `PATCH /contratos/{id}/relatorios/{id}/analise` - Analisar relatório (Admin)

#### Pendências
- `GET /contratos/{id}/pendencias` - Listar pendências
- `POST /contratos/{id}/pendencias` - Criar pendência (Admin)

#### Tabelas Auxiliares
- `GET /perfis` - Listar perfis
- `GET /modalidades` - Listar modalidades
- `GET /status` - Listar status de contratos
- `GET /statusrelatorio` - Listar status de relatórios
- `GET /statuspendencia` - Listar status de pendências

## 📁 Estrutura do Projeto
```
sigescon-fastapi/
├── app/
│   ├── api/
│   │   ├── dependencies.py      # Injeção de dependências
│   │   └── routers/             # Endpoints da API
│   │       ├── auth_router.py
│   │       ├── contrato_router.py
│   │       ├── usuario_router.py
│   │       └── ...
│   ├── core/
│   │   ├── config.py           # Configurações globais
│   │   ├── database.py         # Pool de conexões
│   │   └── security.py         # JWT e hashing
│   ├── repositories/           # Camada de dados
│   │   ├── usuario_repo.py
│   │   ├── contrato_repo.py
│   │   └── ...
│   ├── schemas/                # Modelos Pydantic
│   │   ├── usuario_schema.py
│   │   ├── contrato_schema.py
│   │   └── ...
│   ├── services/               # Lógica de negócio
│   │   ├── usuario_service.py
│   │   ├── contrato_service.py
│   │   └── ...
│   ├── main.py                # Aplicação FastAPI
│   ├── seeder.py              # Popular dados iniciais
│   └── scheduler.py           # Tarefas agendadas
├── database/
│   └── database.sql           # Script do banco
├── tests/                     # Testes automatizados
│   ├── conftest.py
│   ├── test_usuarios.py
│   ├── test_contratos.py
│   └── ...
├── uploads/                   # Arquivos enviados
├── .env.example               # Exemplo de configuração
├── .gitignore
├── pyproject.toml             # Configuração do projeto
├── pytest.ini                 # Configuração de testes
├── README.md
└── run_tests.sh               # Script de validação
```
## 🔄 Fluxo de Trabalho
### Fluxo de Relatórios Fiscais
```mermaid
graph LR
    A[Admin cria Pendência] --> B[Fiscal recebe notificação]
    B --> C[Fiscal submete Relatório]
    C --> D[Admin analisa]
    D --> E{Aprovado?}
    E -->|Sim| F[Pendência Concluída]
    E -->|Não| G[Fiscal recebe feedback]
    G --> C
```
### Níveis de Acesso
| Perfil        | Permissões                                           |
|---------------|------------------------------------------------------|
| Administrador | Acesso total ao sistema                              |
| Gestor        | Visualização de contratos sob sua gestão             |
| Fiscal        | Submissão de relatórios e visualização de pendências |

## 💻 Desenvolvimento
### Convenções de Código
- **PEP 8** - Style guide para Python
- **Type Hints** - Tipagem em todas as funções
- **Docstrings** - Documentação em todos os módulos
- **Async/Await** - Para todas as operações I/O

### Comandos Úteis
```bash
# Formatar código
black app/ tests/

# Verificar tipos
mypy app/

# Ordenar imports
isort app/ tests/

# Verificar estilo
flake8 app/ tests/
```
### Variáveis de Ambiente para Desenvolvimento
```bash
# Debug mode
export DEBUG=True

# Log level
export LOG_LEVEL=DEBUG

# Reload on changes
export RELOAD=True
```
## 🚢 Deploy
### Docker
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
### Docker Compose
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/sigescon
    depends_on:
      - db

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=sigescon
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```
### Heroku
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
### Gunicorn com Uvicorn Workers
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
## 🤝 Contribuindo

- Fork o projeto
- Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
- Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
- Push para a branch (`git push origin feature/AmazingFeature`)
- Abra um Pull Request

### Guidelines

- Escreva testes para novas funcionalidades
- Mantenha a cobertura de testes acima de 80%
- Siga as convenções de código do projeto
- Atualize a documentação quando necessário

## 📄 Licença
Este projeto está licenciado sob a Licença MIT - veja o arquivo `LICENSE` para detalhes.

## 👥 Autores

- **Rafael** - *Desenvolvimento inicial* - [@rafaelcostati](https://github.com/rafaelcostati)

## 🙏 Agradecimentos

- FastAPI pela excelente framework
- Comunidade Python
- Todos os contribuidores

## 📞 Suporte
Para suporte, envie um email para `sememailnomomento@sememail` ou abra uma issue no GitHub.

## 🔗 Links Úteis

- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [Documentação Pydantic](https://pydantic-docs.helpmanual.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pytest Documentation](https://docs.pytest.org/en/latest/)



