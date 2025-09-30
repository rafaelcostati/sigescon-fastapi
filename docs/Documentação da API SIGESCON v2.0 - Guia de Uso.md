### **Documentação da API SIGESCON v2.5 \- Guia de Uso para Desenvolvedores**

**Bem-vindo à API do SIGESCON\!** Este guia irá ajudá-lo a entender como interagir com os nossos recursos, autenticar-se e executar os principais fluxos de trabalho do sistema.

### **🆕 Novidades da Versão 2.5 (Setembro 2025)**

- ✅ **Sistema de Configurações**: Gerenciamento dinâmico de parâmetros do sistema
- ✅ **Pendências Automáticas Configuráveis**: Criação automática com periodicidade definida pelo admin
- ✅ **Lembretes Dinâmicos**: Configuração de quando e com que frequência enviar lembretes
- ✅ **Dashboard Administrativo Completo**: Métricas em tempo real e gestão de pendências
- ✅ **Gestão de Pendências Avançada**: Separação entre vencidas e pendentes
- ✅ **Filtros Avançados**: Contratos por vencimento e status
- ✅ **Alertas de Contratos**: Notificações configuráveis de vencimento

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

**Passo 2 (Fiscal): Verificar pendências e submeter o relatório.**

1. **Login como Fiscal.**
2. **Listar Suas Pendências:**
   * `GET /api/v1/contratos/{contrato_id}/pendencias/` para ver as pendências designadas para ele.
   * O fiscal visualiza quais relatórios precisa enviar.
3. **Submeter o Relatório:**
   * `POST /api/v1/contratos/{contrato_id}/relatorios/` (usando `multipart/form-data`).
   * O corpo deve conter `mes_competencia`, `pendencia_id` e um `arquivo`.
   * **Efeito**: Status da pendência muda automaticamente para "Aguardando Análise".

**Passo 3 (Admin): Analisar e Aprovar o Relatório.**

1. **Login como Admin.**  
2. **Listar Relatórios:**  
   * `GET /api/v1/contratos/{contrato_id}/relatorios/` para ver os relatórios pendentes de análise. Guarde o `relatorio_id`.  
3. **Aprovar o Relatório:**  
   * `PATCH /api/v1/contratos/{contrato_id}/relatorios/{relatorio_id}/analise`.  
   * No corpo, envie o `status_id` correspondente a "Aprovado" e o `aprovador_usuario_id`.

### **5. Fluxo de Status das Pendências**

O sistema implementa transições automáticas de status para melhor controle do workflow:

#### **Estados Possíveis:**
1. **"Pendente"** - Pendência criada, aguardando envio de relatório pelo fiscal
2. **"Aguardando Análise"** - Relatório enviado pelo fiscal, aguardando avaliação do administrador
3. **"Concluída"** - Relatório aprovado pelo administrador
4. **"Cancelada"** - Pendência cancelada pelo administrador

#### **Transições Automáticas:**
- **Criação**: Pendência inicia como "Pendente"
- **Envio de Relatório**: Status muda automaticamente para "Aguardando Análise"
- **Aprovação**: Admin aprova → status vira "Concluída"
- **Rejeição**: Admin rejeita → status volta para "Pendente" (para reenvio)
- **Cancelamento**: Admin cancela → status vira "Cancelada"

#### **Dashboard Fiscal:**
Para verificar pendências designadas:
```
GET /api/v1/contratos/{contrato_id}/pendencias/
```
- Filtra automaticamente pendências do fiscal logado
- Mostra apenas pendências com status "Pendente" (que precisam de ação)

### **6. Paginação e Filtros**

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

### **7. Novos Endpoints Implementados**

#### **7.1. Gerenciamento de Arquivos de Contrato**

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

#### **7.2. Gestão Avançada de Pendências**

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
- **Resposta:** `{"pendentes": 2, "aguardando_analise": 1, "concluidas": 5, "canceladas": 0}`
- **Status das Pendências:**
  - `pendentes`: Aguardando envio de relatório pelo fiscal (Status: "Pendente")
  - `aguardando_analise`: Relatório enviado, aguardando análise do administrador (Status: "Aguardando Análise")
  - `concluidas`: Relatório aprovado pelo administrador (Status: "Concluída")
  - `canceladas`: Pendência cancelada pelo administrador (Status: "Cancelada")

#### **7.3. Arquivos de Relatórios Fiscais**

**Listar arquivos de relatórios por contrato:**
```
GET /api/v1/arquivos/relatorios/contrato/{contrato_id}
```
- **Permissões:** Usuários com acesso ao contrato
- **Resposta:** Lista específica de arquivos de relatórios fiscais
- **Metadados:** Status do relatório, responsável pelo envio, competência

#### **7.4. Funcionalidades de Reenvio**

**Comportamento de Reenvio de Relatórios:**
- **Primeiro envio:** Cria novo relatório na base de dados
- **Reenvios:** Substituem automaticamente o arquivo anterior
- **Status:** Sempre "Pendente de Análise" após reenvio
- **Notificação:** Admin recebe email sobre novo envio

#### **7.5. Gestão de Perfis de Usuário (Múltiplos Perfis)**

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

### **8. Sistema de Configurações (NOVO - v2.5)**

O SIGESCON agora possui um sistema completo de configurações dinâmicas que permite aos administradores ajustar parâmetros do sistema sem necessidade de alteração de código.

#### **8.1. Endpoints de Configuração**

**Listar todas as configurações:**
```
GET /api/v1/config/
```
- **Permissões:** Apenas Administradores
- **Resposta:** Array com todas as configurações do sistema

**Buscar configuração específica:**
```
GET /api/v1/config/{chave}
```
- **Permissões:** Apenas Administradores
- **Parâmetros:** `chave` - Identificador único da configuração
- **Resposta:** Objeto com dados da configuração

**Atualizar configuração:**
```
PATCH /api/v1/config/{chave}
```
- **Permissões:** Apenas Administradores
- **Body:** `{ "valor": "novo_valor" }`
- **Resposta:** Configuração atualizada

#### **8.2. Configurações de Pendências Automáticas**

**Obter intervalo de pendências automáticas:**
```
GET /api/v1/config/pendencias/intervalo-dias
```
- **Permissões:** Apenas Administradores
- **Resposta:** `{ "intervalo_dias": 60 }`
- **Descrição:** Retorna o intervalo em dias configurado para criação automática de pendências

**Atualizar intervalo:**
```
PATCH /api/v1/config/pendencias/intervalo-dias
```
- **Permissões:** Apenas Administradores
- **Body:** `{ "intervalo_dias": 90 }` (mínimo: 1, máximo: 365)
- **Resposta:** Configuração atualizada
- **Exemplo de uso:** Com intervalo de 60 dias, um contrato de 1 ano (365 dias) gerará 6 pendências automáticas

#### **8.3. Configurações de Lembretes**

**Obter configurações de lembretes:**
```
GET /api/v1/config/lembretes/config
```
- **Permissões:** Apenas Administradores
- **Resposta:**
```json
{
  "dias_antes_vencimento_inicio": 30,
  "intervalo_dias_lembrete": 5
}
```
- **Descrição:**
  - `dias_antes_vencimento_inicio`: Quantos dias antes do vencimento começar a enviar lembretes
  - `intervalo_dias_lembrete`: A cada quantos dias repetir os lembretes

**Atualizar configurações de lembretes:**
```
PATCH /api/v1/config/lembretes/config
```
- **Permissões:** Apenas Administradores
- **Body:**
```json
{
  "dias_antes_vencimento_inicio": 30,
  "intervalo_dias_lembrete": 5
}
```
- **Validações:**
  - `dias_antes_vencimento_inicio`: 1-90 dias
  - `intervalo_dias_lembrete`: 1-30 dias
- **Exemplo:** Com 30 dias antes e intervalo de 5 dias, serão enviados lembretes em: 30, 25, 20, 15, 10, 5 dias antes e no vencimento (7 lembretes)

### **9. Pendências Automáticas (NOVO - v2.5)**

Sistema avançado para criação automática de pendências baseado no período do contrato.

#### **9.1. Preview de Pendências Automáticas**

```
POST /api/v1/contratos/{contrato_id}/pendencias-automaticas/preview
```
- **Permissões:** Apenas Administradores
- **Descrição:** Visualiza quais pendências serão criadas sem realmente criá-las
- **Body:** `{ "intervalo_dias": 60 }` (opcional, usa configuração padrão se omitido)
- **Resposta:**
```json
{
  "pendencias_previstas": [
    {
      "numero": 1,
      "titulo": "1º Relatório Fiscal",
      "data_prazo": "2025-11-30",
      "dias_desde_inicio": 60,
      "dias_ate_fim": 305
    },
    {
      "numero": 2,
      "titulo": "2º Relatório Fiscal",
      "data_prazo": "2026-01-29",
      "dias_desde_inicio": 120,
      "dias_ate_fim": 245
    }
  ],
  "total_pendencias": 6,
  "intervalo_utilizado": 60,
  "periodo_contrato": {
    "data_inicio": "2025-10-01",
    "data_fim": "2026-09-30",
    "total_dias": 365
  }
}
```

#### **9.2. Criar Pendências Automáticas**

```
POST /api/v1/contratos/{contrato_id}/pendencias-automaticas/criar
```
- **Permissões:** Apenas Administradores
- **Descrição:** Cria efetivamente as pendências automáticas
- **Body:** `{ "intervalo_dias": 60 }` (opcional)
- **Efeitos:**
  - Cria todas as pendências calculadas
  - Envia email ao fiscal principal com lista completa
  - Envia email ao fiscal substituto (se houver)
- **Resposta:**
```json
{
  "pendencias_criadas": [
    {
      "id": 150,
      "descricao": "1º Relatório Fiscal",
      "data_prazo": "2025-11-30",
      "status": "Pendente"
    }
  ],
  "total_criadas": 6,
  "emails_enviados": [
    "fiscal@example.com",
    "substituto@example.com"
  ]
}
```

### **10. Dashboard Administrativo (NOVO - v2.5)**

Sistema completo de dashboard com métricas em tempo real e gestão de pendências.

#### **10.1. Dashboard Completo**

```
GET /api/v1/dashboard/admin/completo
```
- **Permissões:** Apenas Administradores
- **Descrição:** Retorna todos os contadores e métricas do sistema
- **Resposta:**
```json
{
  "contadores": {
    "total_contratos": 45,
    "contratos_ativos": 38,
    "total_usuarios": 25,
    "total_pendencias": 120,
    "pendencias_vencidas": 8,
    "pendencias_aguardando_analise": 15,
    "relatorios_pendentes_analise": 12
  },
  "alertas": {
    "contratos_proximos_vencimento_30": 5,
    "contratos_proximos_vencimento_60": 8,
    "contratos_proximos_vencimento_90": 12
  }
}
```

#### **10.2. Gestão de Pendências Vencidas**

```
GET /api/v1/dashboard/admin/pendencias-vencidas
```
- **Permissões:** Apenas Administradores
- **Query Params:** `limit` (padrão: 50, máximo: 200)
- **Descrição:** Lista pendências com prazo vencido que ainda não foram concluídas
- **Resposta:**
```json
{
  "pendencias": [
    {
      "id": 45,
      "descricao": "1º Relatório Fiscal",
      "data_prazo": "2025-09-15",
      "dias_atraso": 15,
      "contrato_numero": "CT-2025-001",
      "fiscal_nome": "João Silva",
      "fiscal_email": "joao@example.com",
      "status": "Pendente"
    }
  ],
  "total_pendencias_vencidas": 8,
  "limit": 50
}
```

#### **10.3. Gestão de Pendências Pendentes**

```
GET /api/v1/dashboard/admin/pendencias-pendentes
```
- **Permissões:** Apenas Administradores
- **Query Params:** `limit` (padrão: 50, máximo: 200)
- **Descrição:** Lista pendências ainda não vencidas
- **Resposta:** Estrutura similar às pendências vencidas, mas com `dias_restantes` em vez de `dias_atraso`

#### **10.4. Contratos Próximos ao Vencimento**

```
GET /api/v1/dashboard/admin/contratos-proximos-vencimento
```
- **Permissões:** Apenas Administradores
- **Query Params:** `dias_antecedencia` (padrão: 90, mínimo: 30, máximo: 365)
- **Descrição:** Lista contratos que vencerão dentro do período especificado
- **Resposta:**
```json
{
  "contratos": [
    {
      "id": 10,
      "numero": "CT-2025-010",
      "objeto": "Manutenção de software",
      "data_fim": "2025-12-31",
      "dias_restantes": 92,
      "status": "Ativo",
      "gestor_nome": "Maria Gestora",
      "valor": 50000.00
    }
  ],
  "total": 12,
  "dias_antecedencia": 90
}
```

#### **10.5. Relatórios Pendentes de Análise**

```
GET /api/v1/dashboard/admin/relatorios-pendentes-analise
```
- **Permissões:** Apenas Administradores
- **Descrição:** Lista relatórios enviados pelos fiscais aguardando análise
- **Resposta:**
```json
{
  "relatorios": [
    {
      "id": 78,
      "pendencia_id": 45,
      "pendencia_descricao": "1º Relatório Fiscal",
      "contrato_numero": "CT-2025-001",
      "fiscal_nome": "João Silva",
      "data_envio": "2025-09-28T10:30:00",
      "dias_aguardando": 2,
      "mes_competencia": "2025-09-01",
      "arquivo_nome": "relatorio_setembro.pdf"
    }
  ],
  "total": 12
}
```

#### **10.6. Cancelar Pendência**

```
PATCH /api/v1/dashboard/admin/cancelar-pendencia/{pendencia_id}
```
- **Permissões:** Apenas Administradores
- **Descrição:** Cancela uma pendência existente
- **Efeitos:**
  - Status da pendência muda para "Cancelada"
  - Fiscal recebe email informando o cancelamento
- **Resposta:**
```json
{
  "id": 45,
  "descricao": "1º Relatório Fiscal",
  "status": "Cancelada",
  "cancelada_em": "2025-09-30T14:20:00",
  "email_enviado": true
}
```

### **11. Fluxo Completo: Pendências Automáticas + Lembretes (NOVO)**

Este é o fluxo end-to-end das novas funcionalidades.

#### **Passo 1: Admin Configura o Sistema**

1. **Configurar intervalo de pendências automáticas:**
```
PATCH /api/v1/config/pendencias/intervalo-dias
Body: { "intervalo_dias": 60 }
```

2. **Configurar lembretes:**
```
PATCH /api/v1/config/lembretes/config
Body: {
  "dias_antes_vencimento_inicio": 30,
  "intervalo_dias_lembrete": 5
}
```

#### **Passo 2: Admin Cria Contrato e Pendências Automáticas**

1. **Criar contrato** (via `POST /api/v1/contratos/`)
2. **Visualizar preview:**
```
POST /api/v1/contratos/{id}/pendencias-automaticas/preview
```
3. **Criar pendências:**
```
POST /api/v1/contratos/{id}/pendencias-automaticas/criar
```

#### **Passo 3: Sistema Envia Lembretes Automaticamente**

O scheduler executa diariamente:
- Verifica pendências próximas ao vencimento
- Calcula dias de lembrete baseado nas configurações (30, 25, 20, 15, 10, 5, 0)
- Envia emails aos fiscais nos dias configurados

#### **Passo 4: Admin Monitora via Dashboard**

```
GET /api/v1/dashboard/admin/completo
```
- Visualiza métricas em tempo real
- Identifica pendências vencidas
- Verifica relatórios aguardando análise
- Acompanha contratos próximos ao vencimento

### **12. Tratamento de Erros**

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
