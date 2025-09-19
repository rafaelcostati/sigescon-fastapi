# 🚀 SIGESCON API - Sistema de Gestão de Contratos

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Produção-brightgreen)](README.md)

Sistema robusto de gestão de contratos desenvolvido com **FastAPI**, oferecendo uma API RESTful completa para gerenciamento do ciclo de vida de contratos, relatórios fiscais e fluxos de aprovação. **Projeto em produção** com todas as funcionalidades implementadas e testadas.

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
      - [Arquivos](#arquivos)
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
- 🔐 **Autenticação JWT** - Sistema seguro de autenticação com tokens e migração automática de senhas
- 👥 **Sistema de Perfis Múltiplos** - Permite que um único usuário possua vários perfis (ex: Gestor e Fiscal) com alternância de contexto e permissões dinâmicas.
- 📄 **Gestão de Contratos** - CRUD completo com validações avançadas e soft delete
- 📎 **Upload de Arquivos** - Suporte para múltiplos formatos com validação e organização automática
- 📊 **Relatórios Fiscais** - Fluxo completo de submissão, análise e aprovação/rejeição
- 📅 **Pendências e Prazos** - Sistema automatizado de notificações e lembretes
- 📧 **Notificações por Email** - Integração com SMTP para alertas automáticos personalizados
- 📈 **Paginação e Filtros** - Busca avançada e filtros dinâmicos em todos os módulos
- 🔄 **Soft Delete** - Preservação completa do histórico de dados
- ⚡ **100% Assíncrono** - Alta performance com asyncio e connection pooling
- 🔍 **Sistema de Auditoria** - Log completo de todas as ações críticas
- 📋 **Validações Avançadas** - CPF, CNPJ, datas, arquivos e regras de negócio
- 🎯 **Middleware Customizado** - Logging, auditoria e monitoramento de performance

### Módulos Principais

#### 👤 **Usuários**
- Criação e gestão de usuários com validações completas
- Alteração e reset de senha (própria e administrativa)
- Atribuição de múltiplos perfis com histórico completo de concessões e revogações.
- Listagem paginada com filtros avançados
- Migração automática de senhas do sistema legado

#### 📋 **Contratos**
- Cadastro completo com múltiplos campos e validações
- **Upload múltiplo** de documentos contratuais (até 10 arquivos, 250MB total)
- **Gerenciamento de arquivos** - listar, baixar e excluir arquivos por contrato
- Associação com gestores, fiscais e substitutos
- Filtros avançados por data, status, responsáveis
- Controle de prazos e notificações de vencimento

#### 📝 **Relatórios Fiscais**
- Submissão por fiscais com upload de documentos
- Análise e aprovação/rejeição por administradores
- Sistema de reenvio em caso de rejeição com feedback
- Histórico completo de todas as versões
- Integração com sistema de pendências

#### ⏰ **Pendências**
- Criação automática e manual de tarefas para fiscais
- Controle rigoroso de prazos com múltiplos alertas
- Notificações automáticas em intervalos configuráveis
- Status de conclusão e histórico de alterações

## 🏗 Arquitetura

O projeto segue uma arquitetura em camadas (Clean Architecture) com separação clara de responsabilidades:

```
┌─────────────────┐
│   API Routes    │  ← FastAPI endpoints com validação
├─────────────────┤
│   Middlewares   │  ← Auditoria, CORS, tratamento de erros
├─────────────────┤
│    Services     │  ← Lógica de negócio e orquestração
├─────────────────┤
│  Repositories   │  ← Acesso a dados com queries otimizadas
├─────────────────┤
│    Database     │  ← PostgreSQL com connection pooling
└─────────────────┘
```

### Padrões Implementados
- **Repository Pattern** - Isolamento completo da camada de dados
- **Service Layer** - Centralização de toda lógica de negócio
- **Dependency Injection** - Injeção de dependências nativa do FastAPI
- **DTO Pattern** - Schemas Pydantic para validação e serialização
- **Async/Await** - Operações assíncronas em toda a aplicação
- **Exception Handling** - Tratamento centralizado de exceções customizadas
- **Middleware Pattern** - Cross-cutting concerns (logging, auditoria, CORS)

## 🛠 Tecnologias

### Backend
- **FastAPI** - Framework web moderno e de alta performance
- **Pydantic** - Validação de dados e serialização com type hints
- **asyncpg** - Driver PostgreSQL assíncrono de alta performance
- **python-jose** - Implementação JWT com criptografia
- **passlib + bcrypt** - Hashing seguro de senhas com migração automática
- **aiofiles** - Manipulação assíncrona de arquivos
- **aiosmtplib** - Envio assíncrono de emails
- **APScheduler** - Agendamento de tarefas e lembretes

### Database
- **PostgreSQL 14+** - Banco de dados relacional com índices otimizados
- **Connection Pooling** - Pool de conexões para alta performance
- **Soft Delete** - Preservação de histórico de dados
- **Índices Condicionais** - Otimização para registros ativos

### Testing
- **pytest** - Framework de testes robusto
- **pytest-asyncio** - Suporte completo para testes assíncronos
- **httpx** - Cliente HTTP assíncrono para testes de API
- **Fixtures** - Dados de teste organizados e reutilizáveis

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
O seeder cria a base para o sistema de perfis, status e modalidades.
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

# Ou com Gunicorn + Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Scheduler (Lembretes automáticos)
```bash
# O scheduler é iniciado automaticamente com a aplicação
# Para executar separadamente (opcional):
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
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Métricas**: [http://localhost:8000/metrics](http://localhost:8000/metrics)

### Endpoints Principais

#### Autenticação
- `POST /auth/login` - Realiza o login e retorna o token de acesso, incluindo o `contexto_sessao` com os perfis do usuário.
- `POST /auth/alternar-perfil` - Permite que o usuário alterne seu perfil de sessão atual.
- `GET /auth/contexto` - Retorna o contexto de sessão atual do usuário, incluindo perfil e permissões.
- `GET /auth/dashboard` - Retorna dados contextuais para o dashboard do usuário.
- `GET /auth/permissoes` - Retorna as permissões do usuário para o contexto de sessão atual.

#### Usuários
- `GET /api/v1/usuarios` - Listar usuários paginado com filtros (Admin)
- `POST /api/v1/usuarios` - Criar usuário (Admin)
- `GET /api/v1/usuarios/{id}` - Buscar usuário específico
- `PATCH /api/v1/usuarios/{id}` - Atualizar usuário (Admin)
- `DELETE /api/v1/usuarios/{id}` - Deletar usuário (Admin)
- `GET /api/v1/usuarios/me` - Dados do usuário logado
- `PATCH /api/v1/usuarios/{id}/alterar-senha` - Alterar própria senha
- `PATCH /api/v1/usuarios/{id}/resetar-senha` - Reset de senha (Admin)
- `GET /api/v1/usuarios/{usuario_id}/perfis` - Lista os perfis associados a um usuário.
- `POST /api/v1/usuarios/{usuario_id}/perfis/conceder` - Concede um ou mais perfis a um usuário.
- `POST /api/v1/usuarios/{usuario_id}/perfis/revogar` - Revoga um ou mais perfis de um usuário.

#### Contratos
- `GET /api/v1/contratos` - Listar contratos com filtros avançados e paginação
- `POST /api/v1/contratos` - Criar contrato com upload múltiplo (Admin)
- `GET /api/v1/contratos/{id}` - Detalhes completos do contrato
- `PATCH /api/v1/contratos/{id}` - Atualizar contrato com arquivos adicionais (Admin)
- `DELETE /api/v1/contratos/{id}` - Deletar contrato (Admin)

#### Gerenciamento de Arquivos
- `GET /api/v1/contratos/{id}/arquivos` - Listar arquivos do contrato
- `GET /api/v1/contratos/{id}/arquivos/{arquivo_id}/download` - Download de arquivo
- `DELETE /api/v1/contratos/{id}/arquivos/{arquivo_id}` - Excluir arquivo (Admin)

#### Relatórios
- `GET /api/v1/contratos/{id}/relatorios` - Listar relatórios do contrato
- `POST /api/v1/contratos/{id}/relatorios` - Submeter relatório com arquivo (Fiscal)
- `PATCH /api/v1/contratos/{id}/relatorios/{id}/analise` - Analisar relatório (Admin)

#### Pendências
- `GET /api/v1/contratos/{id}/pendencias` - Listar pendências do contrato
- `POST /api/v1/contratos/{id}/pendencias` - Criar pendência (Admin)

#### Arquivos
- `GET /api/v1/arquivos/{id}/download` - Download de arquivos com controle de acesso

#### Tabelas Auxiliares
- `GET /api/v1/perfis` - Listar perfis de usuário
- `GET /api/v1/modalidades` - Listar modalidades de contratação
- `GET /api/v1/status` - Listar status de contratos
- `GET /api/v1/statusrelatorio` - Listar status de relatórios
- `GET /api/v1/statuspendencia` - Listar status de pendências
- `GET /api/v1/contratados` - Listar contratados com paginação

## 📁 Estrutura do Projeto

```
sigescon-fastapi/
├── app/
│   ├── api/
│   │   ├── dependencies.py         # Injeção de dependências
│   │   ├── permissions.py          # Controle de permissões
│   │   ├── doc_dependencies.py     # Proteção da documentação
│   │   ├── exception_handlers.py   # Tratamento de exceções
│   │   └── routers/                # Endpoints da API
│   │       ├── auth_router.py
│   │       ├── contrato_router.py
│   │       ├── usuario_router.py
│   │       ├── arquivo_router.py
│   │       └── ...
│   ├── core/
│   │   ├── config.py              # Configurações globais
│   │   ├── database.py            # Pool de conexões
│   │   ├── security.py            # JWT e hashing
│   │   └── exceptions.py          # Exceções customizadas
│   ├── middleware/
│   │   ├── audit.py               # Middleware de auditoria
│   │   └── logging.py             # Configuração de logs
│   ├── repositories/              # Camada de dados
│   │   ├── usuario_repo.py
│   │   ├── contrato_repo.py
│   │   └── ...
│   ├── schemas/                   # Modelos Pydantic
│   │   ├── usuario_schema.py
│   │   ├── contrato_schema.py
│   │   └── ...
│   ├── services/                  # Lógica de negócio
│   │   ├── usuario_service.py
│   │   ├── contrato_service.py
│   │   ├── email_service.py
│   │   ├── file_service.py
│   │   └── notification_service.py
│   ├── main.py                   # Aplicação FastAPI
│   ├── seeder.py                 # Popular dados iniciais
│   └── scheduler.py              # Tarefas agendadas
├── database/
│   └── database.sql              # Script completo do banco
├── tests/                        # Testes automatizados
│   ├── conftest.py
│   ├── test_usuarios.py
│   ├── test_contratos.py
│   ├── test_auth.py
│   └── fixtures/                 # Arquivos de teste
├── uploads/                      # Arquivos enviados
├── logs/                         # Arquivos de log
├── .env.example                  # Exemplo de configuração
├── .gitignore
├── pyproject.toml                # Configuração do projeto
├── pytest.ini                   # Configuração de testes
├── README.md
└── run_tests.sh                  # Script de validação
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

O sistema utiliza um modelo de perfis flexível, onde um usuário pode ter múltiplos papéis. As permissões são contextuais, baseadas no perfil que está ativo na sessão do usuário.

| Perfil        | Permissões Principais (quando ativo)                 |
|---------------|------------------------------------------------------|
| **Administrador** | Acesso total ao sistema, incluindo criação de usuários, gestão de perfis e aprovação de relatórios. |
| **Gestor** | Visualização e gestão de contratos sob sua responsabilidade, análise de relatórios da sua equipe. |
| **Fiscal** | Submissão de relatórios para seus contratos designados e visualização de pendências. |

Um usuário com os perfis de **Gestor** e **Fiscal** pode, por exemplo, alternar seu contexto na aplicação para executar tarefas específicas de cada função sem a necessidade de fazer logout.

## 💻 Desenvolvimento

### Convenções de Código

- **PEP 8** - Style guide para Python rigorosamente seguido
- **Type Hints** - Tipagem completa em todas as funções
- **Docstrings** - Documentação detalhada em todos os módulos
- **Async/Await** - Para todas as operações I/O sem exceção
- **Error Handling** - Tratamento específico para cada tipo de erro
- **Soft Delete** - Preservação de dados em todas as entidades

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

# Executar todos os testes
pytest

# Executar servidor de desenvolvimento
uvicorn app.main:app --reload
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

EXPOSE 8000

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
      - JWT_SECRET_KEY=your-secret-key
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

```bash
# Procfile
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Gunicorn com Uvicorn Workers

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Guidelines

- Escreva testes para todas as novas funcionalidades
- Mantenha a cobertura de testes acima de 80%
- Siga rigorosamente as convenções de código do projeto
- Atualize a documentação quando necessário
- Use type hints em todo o código
- Implemente tratamento de erros adequado

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autores

- **Rafael Costa** - *Desenvolvimento e Arquitetura* - [@rafaelcostati](https://github.com/rafaelcostati)

## 🙏 Agradecimentos

- FastAPI pela excelente framework e performance
- Comunidade Python pelo suporte e bibliotecas
- PostgreSQL pela robustez e confiabilidade
- Todos os contribuidores e testadores

## 📞 Suporte

Para suporte técnico:
- 📧 Email: suporte.sigescon@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/rafaelcostati/sigescon-fastapi/issues)
- 📖 Documentação: Acesse `/docs` com o servidor rodando

## 🔗 Links Úteis

- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [Documentação Pydantic](https://pydantic-docs.helpmanual.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pytest Documentation](https://docs.pytest.org/en/latest/)
- [AsyncPG Documentation](https://magicstack.github.io/asyncpg/current/)