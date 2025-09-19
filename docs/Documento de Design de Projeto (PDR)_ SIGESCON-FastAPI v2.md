### **Documento de Design de Projeto (PDR): SIGESCON-FastAPI v2.0**

**Autores:** Rafael Costa

**Status:** Em Produção

---

### **1\. Introdução**

#### **1.1. Propósito do Projeto**

O SIGESCON (Sistema de Gestão de Contratos) é uma API RESTful robusta, desenvolvida para gerenciar o ciclo de vida completo de contratos, principalmente no setor público ou em grandes corporações. O sistema visa automatizar e centralizar o controle sobre contratos, fiscalização, relatórios e prazos, substituindo processos manuais e descentralizados.

Este documento detalha a arquitetura e o design da versão 2.0 do sistema, que migrou de uma base de código Flask para FastAPI, visando maior performance, escalabilidade e manutenibilidade.

#### **1.2. Escopo**

O sistema abrange as seguintes áreas funcionais:

* **Gestão de Entidades:** CRUD completo para Usuários, Contratados, Contratos e tabelas de apoio (Perfis, Status, Modalidades).  
* **Controle de Acesso:** Sistema de autenticação baseado em JWT e um modelo de permissões flexível com múltiplos perfis por usuário.  
* **Fluxo de Fiscalização:** Orquestração do processo de criação de pendências, submissão de relatórios fiscais (com anexos) e o ciclo de aprovação/rejeição.  
* **Automação:** Notificações por e-mail para eventos críticos e lembretes de prazos via tarefas agendadas.  
* **Auditoria e Monitoramento:** Logging detalhado de requisições, ações críticas e performance.

#### **1.3. Objetivos e Critérios de Sucesso**

* **Funcionalidade:** Atingir 100% de paridade com o sistema legado (Flask).  
* **Performance:** Melhorar o tempo de resposta em 30% em comparação com a versão anterior, aproveitando a natureza assíncrona do FastAPI.  
* **Qualidade de Código:** Manter uma cobertura de testes acima de 80%.  
* **Documentação:** Fornecer uma documentação de API completa e interativa via Swagger UI e ReDoc.  
* **Segurança:** Garantir que todas as rotas sejam protegidas adequadamente, com tratamento de exceções e validação de dados robusta.

---

### **2\. Arquitetura do Sistema**

O SIGESCON-FastAPI adota uma arquitetura em camadas (multi-tier) para promover a separação de responsabilidades e facilitar a manutenção e os testes.

#### **2.1. Camadas da Aplicação**

1. **Camada de API (Routers):** Localizada em `app/api/routers/`, esta camada é responsável por definir os endpoints, receber requisições HTTP, validar dados de entrada (usando Pydantic) e formatar as respostas.  
2. **Camada de Serviço (Services):** Em `app/services/`, contém a lógica de negócio da aplicação. Orquestra as operações, invoca os repositórios e implementa as regras de negócio.  
3. **Camada de Acesso a Dados (Repositories):** Em `app/repositories/`, encapsula toda a comunicação com o banco de dados. Contém queries SQL e abstrai os detalhes da persistência de dados.  
4. **Camada Core e Middleware:** Localizada em `app/core/` e `app/middleware/`, provê funcionalidades transversais como configuração, segurança, pool de conexões com o banco, tratamento de exceções e auditoria.

#### **2.2. Tecnologias**

* **Backend:** FastAPI, Pydantic, Uvicorn  
* **Banco de Dados:** PostgreSQL (versão 14+) com o driver `asyncpg` para operações assíncronas.  
* **Autenticação:** JWT com `python-jose` e hashing de senhas com `passlib[bcrypt]`.  
* **Testes:** Pytest com `pytest-asyncio` e `httpx`.  
* **Agendamento de Tarefas:** APScheduler para notificações de prazo.

---

### **3\. Design do Banco de Dados**

O banco de dados PostgreSQL foi projetado para ser relacional e normalizado, com o uso de soft delete (`ativo = TRUE/FALSE`) em tabelas críticas para preservar o histórico de dados.

#### **3.1. Schema (Tabelas Principais)**

* **usuario:** Armazena dados dos usuários, incluindo credenciais e um `perfil_id` legado.  
* **perfil:** Tabela de lookup para os tipos de perfis (Administrador, Gestor, Fiscal).  
* **usuario\_perfil:** Tabela de junção (N:N) que implementa o sistema de múltiplos perfis, associando usuários a perfis.  
* **contrato:** Tabela central que armazena todos os detalhes dos contratos.  
* **pendenciarelatorio:** Registra as pendências de relatórios criadas para os fiscais.  
* **relatoriofiscal:** Armazena os metadados dos relatórios submetidos, incluindo o status do fluxo de aprovação.  
* **arquivo:** Gerencia os metadados dos arquivos que foram enviados, com referência ao contrato.  
* **Tabelas de Apoio:** `contratado`, `modalidade`, `status`, `statuspendencia`, `statusrelatorio`.

#### **3.2. Índices e Otimizações**

* **Índices Únicos Condicionais:** Para garantir a unicidade de campos como `email` e `cpf` apenas para registros ativos (`WHERE ativo IS TRUE`), permitindo que registros "deletados" não bloqueiem novos cadastros.  
* **Índices de Performance:** Criados em colunas frequentemente usadas em cláusulas `WHERE` e `JOIN`, como chaves estrangeiras (`fiscal_id`, `gestor_id`) e datas (`data_fim`).

---

### **4\. Design da API**

A API é versionada (`/api/v1`) e segue os princípios REST. A validação de dados é realizada através de schemas Pydantic, garantindo robustez e clareza.

#### **4.1. Endpoints Principais**

* **/auth**: Endpoints para autenticação, obtenção de token, alternância de perfis e consulta de contexto de sessão.  
* **/api/v1/usuarios**: CRUD completo para usuários e gerenciamento de seus perfis.  
* **/api/v1/contratos**: CRUD de contratos, com suporte a `multipart/form-data` para upload de arquivos.  
* **/api/v1/contratos/{contrato\_id}/pendencias**: Endpoints aninhados para gerenciar as pendências de um contrato específico.  
* **/api/v1/contratos/{contrato\_id}/relatorios**: Endpoints para submissão e análise de relatórios fiscais.

#### **4.2. Schemas (Pydantic)**

Definidos em `app/schemas/`, os schemas garantem:

* **Validação de Tipos:** Conversão e validação automática de tipos de dados.  
* **Validação de Negócio:** Validadores customizados, como o de CPF em `usuario_schema.py`.  
* **Estrutura de Resposta:** Modelos distintos para criação (`Create`), atualização (`Update`), listagem (`List`) e resposta completa (`Paginated`), garantindo que apenas os dados necessários sejam expostos.

---

### **5\. Funcionalidades Detalhadas**

#### **5.1. Sistema de Múltiplos Perfis**

* **Conceito:** Um usuário pode ter vários perfis (ex: "Gestor" e "Fiscal") simultaneamente. As permissões são aplicadas com base no perfil ativo na sessão do usuário.  
* **Implementação:**  
  * A tabela `usuario_perfil` cria a relação N:N.  
  * O `SessionContextService` gerencia o estado da sessão do usuário, incluindo o perfil ativo.  
  * O endpoint `/auth/alternar-perfil` permite ao usuário trocar seu contexto de permissões dinamicamente.

**Detalhamento de Endpoints (Múltiplos Perfis):**

- `GET /api/v1/usuarios/{usuario_id}/perfis` → Lista os perfis ativos do usuário (nome, ids, data de concessão, observações).  
- `GET /api/v1/usuarios/{usuario_id}/perfis/completo` → Retorna dados do usuário com `perfis`, `perfil_ids` e `perfis_texto`.  
- `GET /api/v1/usuarios/{usuario_id}/perfis/validacao` → Retorna capacidades derivadas (pode_ser_fiscal, pode_ser_gestor, pode_ser_admin).  
- `POST /api/v1/usuarios/{usuario_id}/perfis/conceder` → Concede múltiplos perfis a um usuário.  
- `POST /api/v1/usuarios/{usuario_id}/perfis/revogar` → Revoga múltiplos perfis (impede que o usuário fique sem perfis).  
- `POST /usuarios/com-perfis` → Cria usuário e concede perfis na mesma operação (atalho).

**Compatibilidade Legada:**

- A rota `GET /usuarios/{id}` mantém exposição do campo `perfil_id`/`perfil_nome` para compatibilidade com o legado (perfil único), mas não reflete o conjunto completo de perfis. Para a listagem completa, usar os endpoints de múltiplos perfis acima.  
- Na criação (`POST /usuarios/`), o campo `perfil_id` é ignorado e o usuário é criado sem perfil; a concessão deve ocorrer via `/api/v1/usuarios/{id}/perfis/conceder`.

#### **5.2. Sistema de Pendências e Relatórios Fiscais**

O sistema implementa um workflow completo para gestão de relatórios fiscais:

**Fluxo de Pendências:**
1. **Criação:** Admin cria pendência via `POST /api/v1/contratos/{id}/pendencias`
2. **Notificação:** Fiscal recebe email automático com detalhes da tarefa
3. **Cancelamento:** Admin pode cancelar via `PATCH /api/v1/contratos/{id}/pendencias/{id}/cancelar`

**Fluxo de Relatórios:**
1. **Submissão:** Fiscal envia relatório com arquivo via `POST /api/v1/contratos/{id}/relatorios`
2. **Análise:** Admin analisa via `PATCH /api/v1/contratos/{id}/relatorios/{id}/analise`
3. **Resultado:** Aprovação (pendência concluída) ou rejeição (volta para pendente)

**Estados Implementados:**
* **StatusPendencia:** Pendente → Concluída/Cancelada
* **StatusRelatorio:** Pendente de Análise → Aprovado/Rejeitado com Pendência

**Características Técnicas:**
* Primeiro envio cria novo relatório; reenvios substituem arquivo anterior
* Sistema de metadados expandidos (status, responsável, competência)
* Contador para dashboard: `GET /api/v1/contratos/{id}/pendencias/contador`

#### **5.3. Sistema de Notificações por Email**

Sistema robusto de notificações assíncronas implementado:

**Configuração SMTP:**
* **Servidor:** Configurável via variáveis de ambiente (`SMTP_SERVER`, `SMTP_PORT`)
* **Credenciais:** Usuário e senha criptografados (`SENDER_EMAIL`, `SENDER_PASSWORD`)
* **Implementação:** `aiosmtplib` para envio assíncrono não-bloqueante

**Tipos de Notificação:**
* **Pendência criada** → Notifica o fiscal sobre nova tarefa
* **Pendência cancelada** → Informa fiscal que não precisa mais enviar
* **Relatório submetido** → Notifica admin para análise
* **Relatório aprovado** → Confirma aprovação ao fiscal
* **Relatório rejeitado** → Solicita correção com observações
* **Lembretes de prazo** → Alertas automáticos configuráveis

**Características Técnicas:**
* Templates personalizados por tipo de evento
* APScheduler para lembretes periódicos
* Envio assíncrono para não bloquear operações
* Logs de auditoria para controle de envios

#### **5.4. Gerenciamento de Arquivos de Contrato**

**Funcionalidades Implementadas:**
* **Listagem:** `GET /api/v1/contratos/{id}/arquivos` - visualizar todos os arquivos
* **Download Seguro:** `GET /api/v1/contratos/{id}/arquivos/{arquivo_id}/download`
* **Exclusão Controlada:** `DELETE /api/v1/contratos/{id}/arquivos/{arquivo_id}` (admin)
* **Upload Múltiplo:** Suporte para vários arquivos simultaneamente

**Características Técnicas:**
* Validação de permissões por contrato e usuário
* Verificação de integridade dos arquivos no sistema
* Metadados completos (nome, tipo, tamanho, data de criação)
* Cleanup automático (banco + sistema de arquivos)
* Organização em subpastas por ID do contrato
* Hash aleatório para unicidade de nomes

**Separação Contextual:**
* **Arquivos de Contrato:** Documentos oficiais do contrato
* **Arquivos de Relatórios:** PDFs/documentos enviados pelos fiscais
* Endpoint específico: `GET /api/v1/arquivos/relatorios/contrato/{id}`

---

### **6\. Segurança**

* **Autenticação:** O sistema utiliza JWT (`Bearer` token) para autenticação. A função `authenticate_user` em `app/core/security.py` lida com a verificação de senhas e também com a migração transparente de hashes legados (Werkzeug) para o novo formato (bcrypt).  
* **Autorização:** As permissões são gerenciadas em `app/api/permissions.py` através de dependências (`Depends`) que verificam os perfis do usuário na tabela `usuario_perfil`. Decoradores como `@admin_required` simplificam a proteção de rotas.  
* **Tratamento de Exceções:** Handlers globais em `app/api/exception_handlers.py` capturam exceções específicas (de banco de dados, validação, regras de negócio) e genéricas, retornando respostas de erro padronizadas e evitando o vazamento de informações sensíveis.  
* **Proteção de Documentação:** O acesso às rotas `/docs` e `/redoc` é protegido e requer credenciais de administrador via HTTP Basic Auth, conforme definido em `app/api/doc_dependencies.py`.

---

### **7\. Testes**

A estratégia de testes é abrangente e automatizada com `pytest`.

* **Estrutura:** Os testes estão localizados no diretório `tests/` e são nomeados com o prefixo `test_`.  
* **Fixtures:** `conftest.py` e fixtures locais são usados para configurar o ambiente de teste, como a criação de um cliente assíncrono (`async_client`) e a obtenção de tokens de autenticação.  
* **Tipos de Teste:**  
  * **Testes de Integração:** Testam fluxos completos de CRUD e lógicas de negócio que envolvem múltiplos componentes (e.g., `test_full_crud_workflow` em `tests/test_contratados.py`).  
  * **Testes de Permissão:** Verificam se os endpoints respondem corretamente (e.g., com status 403 Forbidden) para usuários com diferentes níveis de acesso.  
  * **Scripts de Validação:** Scripts como `test_multiple_profiles_complete.py` testam fluxos de ponta a ponta, simulando interações complexas de um usuário.

---

### **8\. Deploy e Operações**

* **Configuração:** A aplicação é configurada via variáveis de ambiente, gerenciadas por um arquivo `.env` e carregadas pelo `pydantic-settings` em `app/core/config.py`.  
* **Execução:** A aplicação é servida com Uvicorn. Para produção, recomenda-se o uso de um gerenciador de processos como Gunicorn com workers Uvicorn para paralelismo.  
* **Ciclo de Vida:** O `lifespan` do FastAPI em `app/main.py` gerencia a inicialização e o encerramento de recursos, como o pool de conexões do banco de dados e o agendador de tarefas.  
* **Logging e Auditoria:** Logs de aplicação, banco de dados e autenticação são separados em arquivos distintos. O `AuditMiddleware` registra todas as requisições HTTP e marca ações críticas.

---

### **9\. Riscos e Mitigação**

| Risco | Probabilidade | Impacto | Mitigação |
| :---- | :---- | :---- | :---- |
| **Bugs em produção** | Média | Alto | Suíte de testes abrangente, ambiente de staging, logging detalhado e tratamento de exceções robusto. |
| **Performance degradada** | Baixa | Médio | Uso de arquitetura assíncrona, pool de conexões, índices de banco de dados e monitoramento de requisições lentas via middleware. |
| **Atraso no cronograma** | Média | Médio | Desenvolvimento modular, entregas incrementais e priorização de funcionalidades críticas. |

