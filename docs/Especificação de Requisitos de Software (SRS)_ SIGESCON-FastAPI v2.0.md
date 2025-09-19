### **Especificação de Requisitos de Software (SRS): SIGESCON-FastAPI v2.0**

**Versão:** 1.0

**Autores:** Rafael Costa

**Status:** Aprovado

---

### **1\. Introdução**

#### **1.1. Propósito**

Este documento define os requisitos funcionais e não funcionais para a API do Sistema de Gestão de Contratos (SIGESCON) v2.0. O propósito desta API é fornecer uma plataforma centralizada, segura e performática para gerenciar o ciclo de vida de contratos, seus relatórios de fiscalização e o fluxo de trabalho associado.

Esta especificação destina-se a guiar o desenvolvimento, os testes e a manutenção do sistema, servindo como um ponto de referência para todas as partes interessadas.

#### **1.2. Escopo do Produto**

O SIGESCON-FastAPI é uma API RESTful que serve como o backend para uma aplicação de gestão de contratos. Suas principais funcionalidades incluem:

* **Gestão de Entidades:** Gerenciamento completo (CRUD) de Contratos, Usuários, Contratados e tabelas de apoio.  
* **Controle de Acesso:** Autenticação de usuários e controle de permissões baseado em múltiplos perfis.  
* **Fluxo de Fiscalização:** Automação do processo de solicitação, envio e aprovação de relatórios fiscais.  
* **Gerenciamento de Documentos:** Upload, armazenamento e download seguro de arquivos associados aos contratos.  
* **Sistema de Notificações:** Envio automatizado de e-mails para eventos importantes e lembretes de prazos.

#### **1.3. Definições, Acrônimos e Abreviações**

* **API:** Application Programming Interface  
* **CRUD:** Create, Read, Update, Delete  
* **JWT:** JSON Web Token  
* **PDR:** Documento de Design de Projeto (Project Design Document)  
* **SRS:** Especificação de Requisitos de Software (Software Requirements Specification)  
* **Soft Delete:** Prática de marcar um registro como inativo em vez de excluí-lo fisicamente do banco de dados.

---

### **2\. Descrição Geral**

#### **2.1. Perspectiva do Produto**

O SIGESCON-FastAPI é um sistema de backend autocontido. Ele expõe uma API RESTful que será consumida por uma aplicação frontend (não incluída no escopo deste documento). O sistema depende de um banco de dados PostgreSQL para persistência de dados e, opcionalmente, de um servidor SMTP para envio de e-mails.

#### **2.2. Características do Usuário**

O sistema foi projetado para três perfis principais de usuários:

| Perfil | Descrição das Atividades | Conhecimento Técnico Esperado |
| :---- | :---- | :---- |
| **Administrador** | Gerencia todas as entidades do sistema, incluindo usuários, contratos e configurações. Aprova/rejeita relatórios e tem acesso total aos dados. | Intermediário. Familiaridade com sistemas de gestão. |
| **Gestor** | Supervisiona um conjunto de contratos, acompanha o trabalho dos fiscais, analisa relatórios e gerencia pendências da sua equipe. | Básico. Focado no fluxo de negócio. |
| **Fiscal** | Responsável por acompanhar a execução de contratos específicos, submeter relatórios fiscais e responder a pendências. | Básico. Focado na operação de fiscalização. |

Um mesmo usuário pode acumular múltiplos perfis (ex: ser Gestor e Fiscal).

#### **2.3. Restrições Gerais**

* **Plataforma:** A API deve ser executável em qualquer sistema operacional que suporte Python 3.10+ e PostgreSQL 14+.  
* **Linguagem:** O backend é desenvolvido exclusivamente em Python com o framework FastAPI.  
* **Banco de Dados:** O sistema é projetado para operar com PostgreSQL.  
* **Comunicação:** A comunicação com o cliente deve ser feita via HTTPS, com troca de dados no formato JSON.

---

### **3\. Requisitos Específicos**

#### **3.1. Requisitos Funcionais**

##### **RF01: Gerenciamento de Autenticação e Sessão**

* **RF01.1:** O sistema deve permitir que um usuário se autentique fornecendo e-mail e senha.  
* **RF01.2:** Em caso de sucesso na autenticação, o sistema deve retornar um token de acesso JWT.  
* **RF01.3:** O sistema deve validar o token JWT em todas as requisições a endpoints protegidos.  
* **RF01.4:** Usuários com múltiplos perfis devem poder alternar seu perfil de sessão ativo.  
* **RF01.5:** O sistema deve fornecer um endpoint para que o usuário obtenha os dados de seu próprio perfil (`/usuarios/me`).

##### **RF02: Gerenciamento de Usuários e Perfis**

* **RF02.1:** Apenas Administradores podem criar, atualizar e desativar (soft delete) usuários.  
* **RF02.2:** O sistema deve garantir que os e-mails e CPFs dos usuários ativos sejam únicos.  
* **RF02.3:** O sistema deve validar o formato do CPF no momento do cadastro/atualização.  
* **RF02.4:** Um usuário deve poder alterar sua própria senha, fornecendo a senha antiga.  
* **RF02.5:** Um Administrador deve poder resetar a senha de qualquer usuário.  
* **RF02.6:** Administradores podem conceder e revogar múltiplos perfis para um usuário.  
* **RF02.7:** Um usuário não pode ficar sem nenhum perfil ativo. A revogação do último perfil deve ser bloqueada.

* **RF02.8:** O sistema deve disponibilizar endpoint para listar todos os perfis ativos de um usuário: `GET /api/v1/usuarios/{usuario_id}/perfis`.  
* **RF02.9:** O sistema deve disponibilizar endpoint para retornar informações completas do usuário incluindo arrays de perfis: `GET /api/v1/usuarios/{usuario_id}/perfis/completo`.  
* **RF02.10:** O sistema deve disponibilizar endpoint para validar capacidades de um usuário com base em seus perfis: `GET /api/v1/usuarios/{usuario_id}/perfis/validacao`.  
* **RF02.11:** O sistema deve disponibilizar endpoint para concessão de múltiplos perfis: `POST /api/v1/usuarios/{usuario_id}/perfis/conceder`.  
* **RF02.12:** O sistema deve disponibilizar endpoint para revogação de múltiplos perfis: `POST /api/v1/usuarios/{usuario_id}/perfis/revogar`, impedindo que o usuário fique sem perfis ativos.  
* **RF02.13:** A criação de usuários via `POST /usuarios/` deve ignorar o campo legado `perfil_id` (criando usuários sem perfil). A concessão de perfis deve ocorrer posteriormente via endpoints de múltiplos perfis ou pelo atalho `POST /usuarios/com-perfis`.

##### **RF03: Gerenciamento de Contratos**

* **RF03.1:** Apenas Administradores podem criar, atualizar e desativar (soft delete) contratos.  
* **RF03.2:** Ao criar um contrato, o sistema deve permitir o upload opcional de um arquivo (documento principal do contrato).  
* **RF03.3:** Todos os usuários autenticados podem listar contratos, mas Gestores e Fiscais visualizam apenas os contratos aos quais estão associados, enquanto Administradores visualizam todos.  
* **RF03.4:** O sistema deve fornecer filtros para a listagem de contratos (ex: por gestor, fiscal, status, etc.).  
* **RF03.5:** Ao criar ou alterar um contrato, o sistema deve notificar por e-mail o Gestor e o Fiscal designados.

##### **RF04: Fluxo de Trabalho de Relatórios e Pendências**

* **RF04.1:** Apenas Administradores podem criar pendências de relatório para um contrato.
* **RF04.2:** Ao criar uma pendência, o fiscal do contrato deve ser notificado por e-mail.
* **RF04.3:** Administradores podem cancelar pendências via endpoint específico.
* **RF04.4:** Ao cancelar uma pendência, o fiscal deve ser notificado por e-mail.
* **RF04.5:** Apenas o Fiscal (ou Administrador) associado a um contrato pode submeter um relatório fiscal para aquele contrato.
* **RF04.6:** A submissão de um relatório deve exigir o upload de um arquivo.
* **RF04.7:** Primeiro envio cria novo relatório; reenvios substituem arquivo anterior automaticamente.
* **RF04.8:** Após a submissão, o status da pendência associada deve ser automaticamente alterado para "Concluída".
* **RF04.9:** Apenas Administradores podem analisar (aprovar/rejeitar) um relatório submetido.
* **RF04.10:** O sistema deve prover contador de pendências por status para dashboard.

##### **RF05: Gerenciamento de Arquivos de Contrato**

* **RF05.1:** O sistema deve permitir visualizar todos os arquivos associados a um contrato específico.
* **RF05.2:** Usuários autenticados podem fazer download de arquivos de contratos aos quais têm acesso.
* **RF05.3:** Apenas Administradores podem excluir arquivos de contratos.
* **RF05.4:** O sistema deve suportar upload múltiplo de arquivos durante criação/edição de contratos.
* **RF05.5:** O sistema deve separar arquivos de contrato de arquivos de relatórios fiscais.
* **RF05.6:** Metadados dos arquivos devem incluir nome, tipo, tamanho e data de criação.
* **RF05.7:** O sistema deve garantir integridade física dos arquivos no sistema de arquivos.

##### **RF06: Sistema de Notificações por Email**

* **RF06.1:** O sistema deve enviar notificação quando uma pendência for criada.
* **RF06.2:** O sistema deve enviar notificação quando uma pendência for cancelada.
* **RF06.3:** O sistema deve enviar notificação quando um relatório for submetido.
* **RF06.4:** O sistema deve enviar notificação quando um relatório for aprovado.
* **RF06.5:** O sistema deve enviar notificação quando um relatório for rejeitado.
* **RF06.6:** O sistema deve suportar lembretes automáticos de prazo configuráveis.
* **RF06.7:** Todas as notificações devem usar templates personalizados por tipo de evento.
* **RF06.8:** O envio de emails deve ser assíncrono para não bloquear operações.

#### **3.2. Requisitos de Interface Externa**

* **RNI01:** A API deve ser acessível via protocolo HTTP/HTTPS.  
* **RNI02:** A troca de dados deve ocorrer exclusivamente através do formato JSON.  
* **RNI03:** A API deve fornecer documentação interativa (Swagger UI/ReDoc) em um endpoint específico (`/docs`, `/redoc`), protegido por autenticação.

#### **3.3. Requisitos Não Funcionais**

##### **RNF01: Performance**

* **RNF01.1:** O tempo de resposta médio para requisições de leitura (GET) deve ser inferior a 200ms sob carga normal.  
* **RNF01.2:** Requisições que demorem mais de 2 segundos para serem processadas devem ser registradas em log para análise.  
* **RNF01.3:** O sistema deve utilizar um pool de conexões com o banco de dados para otimizar o acesso e reutilizar conexões.

##### **RNF02: Segurança**

* **RNF02.1:** Todas as senhas de usuários devem ser armazenadas no banco de dados utilizando um algoritmo de hashing forte (bcrypt).  
* **RNF02.2:** O sistema deve ser capaz de validar senhas em formato legado (Werkzeug) e migrá-las para bcrypt de forma transparente no primeiro login bem-sucedido.  
* **RNF02.3:** O acesso a arquivos para download deve ser restrito a usuários com permissão no contrato associado.  
* **RNF02.4:** Tokens JWT devem ter um tempo de expiração configurável.

##### **RNF03: Confiabilidade e Disponibilidade**

* **RNF03.1:** O sistema deve implementar um health check (`/health`) que verifique a conectividade com o banco de dados e o status de serviços essenciais.  
* **RNF03.2:** Erros de banco de dados e exceções não tratadas devem ser capturados por handlers globais para evitar a queda da aplicação e retornar uma resposta de erro padronizada.  
* **RNF03.3:** O ciclo de vida da aplicação (startup/shutdown) deve gerenciar corretamente a inicialização e o fechamento de recursos, como o pool de conexões do banco.

##### **RNF04: Manutenibilidade e Auditoria**

* **RNF04.1:** O sistema deve registrar em logs todas as requisições HTTP, com ênfase em ações críticas (criação, alteração, exclusão).  
* **RNF04.2:** Os logs devem ser separados por contexto (aplicação, auditoria, banco de dados, autenticação).  
* **RNF04.3:** O código deve seguir as convenções de estilo PEP 8 e utilizar type hints para clareza e manutenibilidade.

---

### **4\. Apêndice**

* **A. Modelo de Dados:** O script completo de criação do banco de dados, incluindo tabelas, índices e relacionamentos, encontra-se em `database/database.sql` e `database/multiplo.sql`.  
* **B. Especificação da API (OpenAPI):** A especificação completa da API é gerada automaticamente e pode ser acessada no endpoint `/openapi.json` quando a aplicação está em execução.

