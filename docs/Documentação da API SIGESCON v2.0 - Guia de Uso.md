### **Documentação da API SIGESCON v2.0 \- Guia de Uso para Desenvolvedores**

**Bem-vindo à API do SIGESCON\!** Este guia irá ajudá-lo a entender como interagir com os nossos recursos, autenticar-se e executar os principais fluxos de trabalho do sistema.

### **1\. Visão Geral e Conceitos**

A API do SIGESCON é uma interface RESTful construída com FastAPI que permite o gerenciamento completo do ciclo de vida de contratos. A comunicação é feita via HTTPS e todos os dados são trocados no formato JSON.

**Conceitos Chave:**

* **Autenticação JWT:** O acesso aos endpoints é protegido e requer um `Bearer Token` no cabeçalho `Authorization`.  
* **Perfis Múltiplos e Contexto de Sessão:** Um usuário pode ter vários perfis (ex: Fiscal, Gestor). A cada login, uma `contexto_sessao` é retornada, indicando o perfil ativo e os perfis disponíveis. As permissões do usuário dependem do perfil ativo, que pode ser alternado.  
* **Endpoints Protegidos:** Quase todos os endpoints, exceto `/auth/login`, são protegidos e exigem autenticação.

### **2\. Guia de Início Rápido (Quickstart)**

Vamos fazer as primeiras chamadas à API em 3 passos. Use o usuário administrador padrão para este guia.

**Usuário Padrão (do `.env`):**

* **Email:** `admin@sigescon.com`  
* **Senha:** `Admin@123`

#### **Passo 1: Autenticação e Obtenção do Token**

Primeiro, faça uma requisição `POST` para o endpoint `/auth/login` para obter o seu token de acesso. A requisição deve ser do tipo `x-www-form-urlencoded`.

**Requisição:**

POST /auth/login

Content-Type: application/x-www-form-urlencoded

username=admin@sigescon.com\&password=Admin@123

**Resposta de Sucesso (200 OK):**

{

  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",

  "token_type": "bearer",

  "contexto_sessao": {

    "usuario_id": 1,

    "perfil_ativo_id": 1,

    "perfil_ativo_nome": "Administrador",

    "perfis_disponiveis": \[

      {

        "id": 1,

        "nome": "Administrador",

        "pode_ser_selecionado": true,

        "descricao": "Acesso total ao sistema"

      }

    \],

    "pode_alternar": false,

    "sessao_id": "mock-session-1"

  },

  "requer_selecao_perfil": false,

  "mensagem": null

}

Nota: O objeto retornado em `/usuarios/me` reflete o perfil legado (`perfil_id`/`perfil_nome`) para compatibilidade. Para listar TODOS os perfis de um usuário no sistema de múltiplos perfis, utilize os endpoints da seção "Gestão de Perfis de Usuário" abaixo.

**Guarde o valor de `access_token`.** Você precisará dele para todas as chamadas futuras.

#### **Passo 2: Verificando seu Perfil**

Agora, vamos usar o token para aceder a um endpoint protegido e obter os dados do usuário logado.

**Requisição:**

GET /api/v1/usuarios/me

Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

**Resposta de Sucesso (200 OK):**

{

  "nome": "Administrador do Sistema",

  "email": "admin@sigescon.com",

  "cpf": "00000000000",

  "matricula": null,

  "perfil_id": 1,

  "id": 1,

  "ativo": true,

  "created_at": "2025-09-18T15:30:00.000Z",

  "updated_at": "2025-09-18T15:30:00.000Z",

  "perfil_nome": "Administrador"

}

#### **Passo 3: Listando Recursos (Contratados)**

Finalmente, vamos fazer uma chamada para listar um recurso principal do sistema, como os contratados.

**Requisição:**

GET /api/v1/contratados/?page=1\&per_page=5

Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

**Resposta de Sucesso (200 OK):**

{

  "data": \[

    {

      "nome": "Empresa Teste LTDA",

      "email": "contato@empresateste.com",

      "cnpj": "12345678000123",

      "cpf": null,

      "telefone": "(91) 99999-9999",

      "id": 1,

      "ativo": true

    }

  \],

  "total_items": 1,

  "total_pages": 1,

  "current_page": 1,

  "per_page": 5

}

Parabéns! Você autenticou-se e consumiu com sucesso um endpoint da API SIGESCON.

### **3. Autenticação e Gestão de Perfis**

O sistema de autenticação é flexível para lidar com usuários que possuem múltiplos papéis.

#### **Fluxo de Login e Contexto**

1. O usuário envia as credenciais para `/auth/login`.  
2. A API retorna o `access_token` e o `contexto_sessao`.  
3. O `contexto_sessao` informa o perfil que está **ativo por defeito** (o de maior prioridade: Administrador > Gestor > Fiscal) e a lista de todos os `perfis_disponiveis`.  
4. O cliente (frontend) deve usar o `perfil_ativo_nome` para ajustar a sua interface e as opções disponíveis.

#### **Alternando o Perfil Ativo**

Se o campo `pode_alternar` no contexto for `true`, o usuário pode mudar o seu perfil ativo para aceder a diferentes funcionalidades.

**Requisição:**

POST /auth/alternar-perfil

Authorization: Bearer <seu_token>

Content-Type: application/json

{

  "novo_perfil_id": 3,

  "justificativa": "Mudando para o modo de fiscalização"

}

* `novo_perfil_id`: O `id` do perfil desejado, obtido da lista `perfis_disponiveis`.

**Resposta de Sucesso (200 OK):** A API retornará um novo objeto `contexto_sessao` atualizado, que o cliente deve usar para atualizar o estado da aplicação.

### **4. Receitas de Workflows (Exemplos Práticos)**

#### **Receita 1: Fluxo Completo de Fiscalização de Relatório**

Este é o fluxo de negócio mais importante do sistema.

**Personagens:**

* **Admin:** `admin@sigescon.com`  
* **Fiscal:** `fiscal.teste@example.com`

**Passo 1 (Admin): Criar um contrato e uma pendência.**

1. **Login como Admin** (veja Quickstart).  
2. **Criar o Contrato:**  
   * `POST /api/v1/contratos/` (usando `multipart/form-data`) com os dados do contrato, designando o `fiscal_id` para o usuário Fiscal. Guarde o `id` do contrato criado.  
3. **Criar a Pendência:**  
   * `POST /api/v1/contratos/{contrato_id}/pendencias/` com a descrição da pendência e a data de prazo. Guarde o `id` da pendência.

**Passo 2 (Fiscal): Submeter o relatório.**

1. **Login como Fiscal.**  
2. **Listar Pendências:**  
   * `GET /api/v1/contratos/{contrato_id}/pendencias/` para ver as pendências em aberto.  
3. **Submeter o Relatório:**  
   * `POST /api/v1/contratos/{contrato_id}/relatorios/` (usando `multipart/form-data`).  
   * O corpo deve conter `mes_competencia`, `pendencia_id` e um `arquivo`.

**Passo 3 (Admin): Analisar e Aprovar o Relatório.**

1. **Login como Admin.**  
2. **Listar Relatórios:**  
   * `GET /api/v1/contratos/{contrato_id}/relatorios/` para ver os relatórios pendentes de análise. Guarde o `relatorio_id`.  
3. **Aprovar o Relatório:**  
   * `PATCH /api/v1/contratos/{contrato_id}/relatorios/{relatorio_id}/analise`.  
   * No corpo, envie o `status_id` correspondente a "Aprovado" e o `aprovador_usuario_id`.

### **5. Paginação e Filtros**

Endpoints que retornam listas de recursos (como `/contratos`, `/contratados`, `/usuarios`) são paginados.

**Query Parameters:**

* `page` (int): O número da página que deseja aceder. Padrão: 1\.  
* `per_page` (int): O número de itens por página. Padrão: 10, Máximo: 100\.

**Estrutura da Resposta Paginada:**

{

  "data": \[ ... lista de itens ... \],

  "total_items": 150,

  "total_pages": 15,

  "current_page": 1,

  "per_page": 10

}

Muitos endpoints também aceitam query parameters adicionais para **filtragem**. Consulte a documentação do Swagger (`/docs`) para ver os filtros disponíveis em cada rota.

### **6. Novos Endpoints Implementados**

#### **6.1. Gerenciamento de Arquivos de Contrato**

**Listar arquivos de um contrato:**
```
GET /api/v1/contratos/{contrato_id}/arquivos
```
- **Permissões:** Usuários com acesso ao contrato
- **Resposta:** Lista de arquivos com metadados (nome, tipo, tamanho, data)

**Download de arquivo específico:**
```
GET /api/v1/contratos/{contrato_id}/arquivos/{arquivo_id}/download
```
- **Permissões:** Usuários com acesso ao contrato
- **Resposta:** Stream do arquivo para download

**Excluir arquivo (somente Admin):**
```
DELETE /api/v1/contratos/{contrato_id}/arquivos/{arquivo_id}
```
- **Permissões:** Apenas Administradores
- **Resposta:** Confirmação de exclusão

#### **6.2. Gestão Avançada de Pendências**

**Cancelar pendência:**
```
PATCH /api/v1/contratos/{contrato_id}/pendencias/{pendencia_id}/cancelar
```
- **Permissões:** Apenas Administradores
- **Resposta:** Pendência atualizada com status "Cancelada"
- **Efeito:** Fiscal recebe email de cancelamento

**Contador de pendências para dashboard:**
```
GET /api/v1/contratos/{contrato_id}/pendencias/contador
```
- **Permissões:** Usuários com acesso ao contrato
- **Resposta:** `{"pendentes": 2, "analise_pendente": 1, "concluidas": 5, "canceladas": 0}`

#### **6.3. Arquivos de Relatórios Fiscais**

**Listar arquivos de relatórios por contrato:**
```
GET /api/v1/arquivos/relatorios/contrato/{contrato_id}
```
- **Permissões:** Usuários com acesso ao contrato
- **Resposta:** Lista específica de arquivos de relatórios fiscais
- **Metadados:** Status do relatório, responsável pelo envio, competência

#### **6.4. Funcionalidades de Reenvio**

**Comportamento de Reenvio de Relatórios:**
- **Primeiro envio:** Cria novo relatório na base de dados
- **Reenvios:** Substituem automaticamente o arquivo anterior
- **Status:** Sempre "Pendente de Análise" após reenvio
- **Notificação:** Admin recebe email sobre novo envio

#### **6.5. Gestão de Perfis de Usuário (Múltiplos Perfis)**

O SIGESCON suporta múltiplos perfis por usuário através da relação `usuario_perfil`. Utilize estes endpoints para listar, conceder e revogar perfis:

- `GET /api/v1/usuarios/{usuario_id}/perfis`
  - Lista todos os perfis ativos do usuário.
  - Permissões: o próprio usuário ou Administrador.
  - Exemplo de resposta:
  ```json
  [
    {
      "id": 10,
      "usuario_id": 5,
      "perfil_id": 2,
      "perfil_nome": "Gestor",
      "data_concessao": "2025-09-19T12:34:56Z",
      "observacoes": null,
      "ativo": true
    },
    {
      "id": 11,
      "usuario_id": 5,
      "perfil_id": 3,
      "perfil_nome": "Fiscal",
      "data_concessao": "2025-09-19T12:40:00Z",
      "observacoes": "concessão em lote",
      "ativo": true
    }
  ]
  ```

- `GET /api/v1/usuarios/{usuario_id}/perfis/completo`
  - Retorna dados do usuário com arrays `perfis` (nomes), `perfil_ids` e `perfis_texto`.
  - Permissões: o próprio usuário ou Administrador.
  - Exemplo de resposta:
  ```json
  {
    "id": 5,
    "nome": "João Silva",
    "email": "joao@example.com",
    "matricula": "12345",
    "ativo": true,
    "perfis": ["Fiscal", "Gestor"],
    "perfil_ids": [3, 2],
    "perfis_texto": "Fiscal, Gestor"
  }
  ```

- `GET /api/v1/usuarios/{usuario_id}/perfis/validacao`
  - Retorna capacidades derivadas dos perfis do usuário (p.ex., se pode ser fiscal, gestor, admin).
  - Permissões: o próprio usuário ou Administrador.

- `POST /api/v1/usuarios/{usuario_id}/perfis/conceder`
  - Concede múltiplos perfis a um usuário.
  - Permissões: Administrador.
  - Corpo (JSON): `{ "perfil_ids": [1, 2, 3], "observacoes": "opcional" }`

- `POST /api/v1/usuarios/{usuario_id}/perfis/revogar`
  - Revoga múltiplos perfis do usuário (não permite deixar o usuário sem perfis ativos).
  - Permissões: Administrador.
  - Corpo (JSON): `{ "perfil_ids": [2], "motivo": "opcional" }`

Observações importantes:
- A rota `GET /usuarios/{id}` (sem prefixo `/api/v1`) expõe o campo legado `perfil_id` apenas para compatibilidade.
- Para listar todos os perfis de um usuário, utilize os endpoints acima.
- Na criação de usuário (`POST /usuarios/`), o campo `perfil_id` é sempre ignorado (criação sem perfil). Conceda perfis via `POST /api/v1/usuarios/{id}/perfis/conceder` ou use o atalho `POST /usuarios/com-perfis`.

### **7. Tratamento de Erros**

A API usa códigos de status HTTP padrão e retorna um corpo de resposta JSON para fornecer detalhes sobre o erro.

**Estrutura da Resposta de Erro:**

{

  "error": true,

  "error\_type": "ResourceNotFoundException",

  "message": "Contrato não encontrado",

  "details": {},

  "path": "/api/v1/contratos/999"

}

**Códigos de Erro Comuns:**

| Código | Significado | Causa Comum |
| :---- | :---- | :---- |
| **401 Unauthorized** | Token JWT inválido, expirado ou não fornecido. | Falha no login; token ausente no cabeçalho `Authorization`. |
| **403 Forbidden** | O usuário autenticado não tem permissão para aceder ao recurso. | Um Fiscal a tentar criar um contrato; um usuário a tentar ver um contrato de outro fiscal. |
| **404 Not Found** | O recurso solicitado não existe. | Um ID inválido foi fornecido na URL (ex: `/contratos/9999`). |
| **409 Conflict** | A requisição não pôde ser concluída devido a um conflito com o estado atual do recurso. | Tentar criar um usuário com um e-mail que já existe. |
| **422 Unprocessable Entity** | A sintaxe da requisição está correta, mas os dados falharam na validação. | CPF inválido, e-mail mal formatado, campos obrigatórios em falta no corpo da requisição. |

---

**Para uma referência completa e interativa de todos os endpoints, schemas e parâmetros, por favor, consulte a nossa documentação Swagger em `/docs` com a aplicação em execução.**  
