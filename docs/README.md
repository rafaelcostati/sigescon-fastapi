# 📚 Documentação SIGESCON v2.5

Bem-vindo à documentação completa do **SIGESCON** (Sistema de Gestão de Contratos) versão 2.5.

---

## 📋 Índice de Documentos

### 🚀 Documentação Principal

#### 1. **CLAUDE.md** (Raiz do Projeto)
**Descrição:** Documentação técnica completa e atualizada do projeto  
**Público:** Desenvolvedores e equipe técnica  
**Conteúdo:**
- Visão geral do projeto
- Arquitetura do sistema
- Stack tecnológica
- Estrutura de diretórios
- API Endpoints completos
- Sistema de permissões
- Funcionalidades principais
- Status da migração Flask → FastAPI
- Comandos úteis

**📍 Localização:** `../CLAUDE.md`

---

### 📖 Guias de Uso

#### 2. **Documentação da API SIGESCON v2.5 - Guia de Uso.md**
**Descrição:** Guia completo para desenvolvedores consumirem a API  
**Público:** Desenvolvedores frontend e integrações  
**Conteúdo:**
- Quickstart (primeiros passos)
- Autenticação e gestão de perfis
- Workflows práticos (receitas)
- Paginação e filtros
- Todos os endpoints documentados
- Sistema de configurações (NOVO v2.5)
- Pendências automáticas (NOVO v2.5)
- Dashboard administrativo (NOVO v2.5)
- Lembretes configuráveis (NOVO v2.5)
- Tratamento de erros

**📍 Localização:** `Documentação da API SIGESCON v2.0 - Guia de Uso.md`

---

#### 3. **FUNCIONALIDADES_v2.5.md** (NOVO)
**Descrição:** Guia de funcionalidades para usuários finais  
**Público:** Administradores, Gestores e Fiscais  
**Conteúdo:**
- Visão geral das novidades
- Guia para administradores
- Guia para fiscais
- Guia para gestores
- Tutoriais passo a passo
- Perguntas frequentes (FAQ)
- Exemplos práticos

**📍 Localização:** `FUNCIONALIDADES_v2.5.md`

---

### 🏗️ Arquitetura e Design

#### 4. **Documento de Arquitetura de Software (SAD).md**
**Descrição:** Arquitetura detalhada do sistema  
**Público:** Arquitetos de software e desenvolvedores sênior  
**Conteúdo:**
- Introdução e propósito
- Visão arquitetural
- Padrões e decisões arquiteturais
- Estrutura em camadas
- Visão de processos (runtime)
- Visão de dados
- Componentes transversais
- Atributos de qualidade

**📍 Localização:** `Documento de Arquitetura de Software (SAD).md`

---

#### 5. **Documento de Design de Projeto (PDR): SIGESCON-FastAPI v2.md**
**Descrição:** Design detalhado de componentes  
**Público:** Desenvolvedores  
**Conteúdo:**
- Design de classes
- Schemas e modelos
- Fluxos de dados
- Interações entre componentes

**📍 Localização:** `Documento de Design de Projeto (PDR)_ SIGESCON-FastAPI v2.md`

---

### 📝 Requisitos e Especificações

#### 6. **Especificação de Requisitos de Software (SRS): SIGESCON-FastAPI v2.0.md**
**Descrição:** Requisitos funcionais e não-funcionais  
**Público:** Analistas e desenvolvedores  
**Conteúdo:**
- Requisitos funcionais
- Requisitos não-funcionais
- Casos de uso
- Regras de negócio

**📍 Localização:** `Especificação de Requisitos de Software (SRS)_ SIGESCON-FastAPI v2.0.md`

---

### 🔄 Changelog e Atualizações

#### 7. **CHANGELOG_v2.5.md** (NOVO)
**Descrição:** Changelog completo da versão 2.5  
**Público:** Todos os usuários e desenvolvedores  
**Conteúdo:**
- Resumo executivo
- Novas funcionalidades detalhadas
- Melhorias técnicas
- Impacto das mudanças
- Migrações de banco de dados
- Testes recomendados
- Checklist de deploy
- Próximos passos

**📍 Localização:** `CHANGELOG_v2.5.md`

---

### 🛠️ Guias Técnicos Específicos

#### 8. **CLAUDE_SETUP.md**
**Descrição:** Setup inicial do projeto  
**Público:** Novos desenvolvedores  
**Conteúdo:**
- Instalação de dependências
- Configuração do ambiente
- Primeiro run
- Troubleshooting

**📍 Localização:** `CLAUDE_SETUP.md`

---

#### 9. **DATABASE_RESET.md**
**Descrição:** Procedimentos de reset e manutenção do banco  
**Público:** DBAs e desenvolvedores  
**Conteúdo:**
- Reset completo do banco
- Migrations
- Backup e restore
- Troubleshooting de banco

**📍 Localização:** `DATABASE_RESET.md`

---

### 📌 Documentação Específica

#### 10. **LEMBRETES_PENDENCIAS.md** (Raiz do Projeto - NOVO)
**Descrição:** Documentação técnica completa do sistema de lembretes  
**Público:** Desenvolvedores  
**Conteúdo:**
- Visão geral
- Funcionalidades implementadas
- Arquitetura
- Fluxo de funcionamento
- Exemplos de uso
- Configuração inicial
- Benefícios
- Testes

**📍 Localização:** `../LEMBRETES_PENDENCIAS.md`

---

## 🆕 O que há de novo na v2.5?

### Funcionalidades Principais:
1. **Sistema de Configurações Dinâmicas**
   - Gerenciamento de parâmetros via interface
   - Sem necessidade de acesso ao código
   - Auditoria de alterações

2. **Pendências Automáticas Configuráveis**
   - Criação inteligente baseada em período
   - Preview antes de criar
   - Nomenclatura sequencial automática

3. **Lembretes Dinâmicos**
   - Configuração de quando começar
   - Intervalo personalizável
   - Preview de quantos lembretes serão enviados

4. **Dashboard Administrativo Completo**
   - Métricas em tempo real
   - Gestão de pendências vencidas/pendentes
   - Alertas de contratos próximos ao vencimento
   - Relatórios pendentes de análise

5. **Interface de Administração**
   - Página dedicada no frontend
   - Cards organizados por funcionalidade
   - Feedback visual em tempo real

### Documentos Criados/Atualizados:
- ✅ **CLAUDE.md** - Atualizado para v2.5
- ✅ **Documentação da API** - Incluídas todas as novas funcionalidades
- ✅ **CHANGELOG_v2.5.md** - Changelog completo
- ✅ **FUNCIONALIDADES_v2.5.md** - Guia para usuários finais
- ✅ **LEMBRETES_PENDENCIAS.md** - Documentação técnica específica
- ✅ **README.md (este arquivo)** - Índice atualizado

---

## 📂 Estrutura de Pastas

```
backend-contratos-FASTAPI/
├── CLAUDE.md                          # Documentação principal
├── LEMBRETES_PENDENCIAS.md            # Doc específica de lembretes
├── README.md                          # Readme do projeto
│
├── docs/                              # Pasta de documentação
│   ├── README.md                      # Este arquivo (índice)
│   ├── CHANGELOG_v2.5.md              # Changelog da v2.5
│   ├── FUNCIONALIDADES_v2.5.md        # Guia de funcionalidades
│   ├── Documentação da API SIGESCON v2.5 - Guia de Uso.md
│   ├── Documento de Arquitetura de Software (SAD).md
│   ├── Documento de Design de Projeto (PDR)_ SIGESCON-FastAPI v2.md
│   ├── Especificação de Requisitos de Software (SRS)_ SIGESCON-FastAPI v2.0.md
│   ├── CLAUDE_SETUP.md
│   └── DATABASE_RESET.md
│
├── migrations/                        # Scripts de migração
│   └── add_lembretes_config.sql      # Migração v2.5
│
└── app/                               # Código fonte
    └── ... (estrutura da aplicação)
```

---

## 🎯 Guia de Leitura por Perfil

### 👨‍💻 Novo Desenvolvedor:
1. **CLAUDE.md** - Entenda o projeto
2. **CLAUDE_SETUP.md** - Configure seu ambiente
3. **Documento de Arquitetura (SAD).md** - Entenda a arquitetura
4. **Documentação da API** - Aprenda os endpoints

### 🔧 Desenvolvedor Experiente:
1. **CHANGELOG_v2.5.md** - Veja o que mudou
2. **LEMBRETES_PENDENCIAS.md** - Entenda as novas funcionalidades
3. **Documentação da API** - Consulte os novos endpoints

### 👨‍💼 Administrador do Sistema:
1. **FUNCIONALIDADES_v2.5.md** - Guia completo de uso
2. **Documentação da API** - Seção de configurações
3. **FAQ** - Perguntas frequentes

### 👷 Fiscal/Gestor:
1. **FUNCIONALIDADES_v2.5.md** - Seção específica para seu perfil
2. **FAQ** - Perguntas frequentes

### 🏗️ Arquiteto de Software:
1. **Documento de Arquitetura (SAD).md**
2. **CLAUDE.md** - Seção de arquitetura
3. **Documento de Design (PDR).md**

### 📊 Analista:
1. **Especificação de Requisitos (SRS).md**
2. **FUNCIONALIDADES_v2.5.md**
3. **CHANGELOG_v2.5.md**

---

## 🔍 Busca Rápida

### Procurando informações sobre:

**Autenticação e Segurança:**
- CLAUDE.md → Seção "Sistema de Autenticação"
- Documentação da API → Seção "3. Autenticação e Gestão de Perfis"

**Endpoints da API:**
- CLAUDE.md → Seção "API Endpoints"
- Documentação da API → Completa

**Configurações do Sistema:**
- Documentação da API → Seção "8. Sistema de Configurações"
- FUNCIONALIDADES_v2.5.md → Tutorial de configuração

**Pendências Automáticas:**
- Documentação da API → Seção "9. Pendências Automáticas"
- FUNCIONALIDADES_v2.5.md → "Criar Pendências Automáticas"

**Lembretes:**
- LEMBRETES_PENDENCIAS.md → Documentação completa
- FUNCIONALIDADES_v2.5.md → "Configurar Lembretes"

**Dashboard:**
- Documentação da API → Seção "10. Dashboard Administrativo"
- FUNCIONALIDADES_v2.5.md → "Dashboard Melhorado"

**Arquitetura:**
- Documento de Arquitetura (SAD).md → Completo
- CLAUDE.md → Visão geral

**Banco de Dados:**
- DATABASE_RESET.md → Manutenção
- migrations/ → Scripts SQL

---

## 📞 Suporte e Contribuição

### Encontrou um erro na documentação?
- Abra uma issue
- Entre em contato com a equipe

### Quer contribuir?
- Leia CLAUDE.md
- Siga os padrões estabelecidos
- Atualize a documentação relevante

### Precisa de ajuda?
- Consulte a documentação apropriada acima
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🔄 Versionamento da Documentação

| Versão | Data | Principais Mudanças |
|--------|------|---------------------|
| 2.5 | 30/09/2025 | Sistema de configurações, pendências automáticas, lembretes dinâmicos, dashboard completo |
| 2.0 | 18/09/2025 | Migração completa Flask → FastAPI, múltiplos perfis, contexto de sessão |
| 1.0 | Anterior | Sistema original em Flask |

---

## 📜 Licença

Este projeto e sua documentação são propriedade da organização e destinam-se exclusivamente para uso interno.

---

**Última Atualização:** 30/09/2025  
**Versão da Documentação:** 2.5  
**Mantido por:** Equipe SIGESCON

---

*Para sugestões de melhoria desta documentação, entre em contato com a equipe de desenvolvimento.*
