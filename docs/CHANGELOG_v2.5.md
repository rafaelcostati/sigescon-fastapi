# 🚀 SIGESCON v2.5 - Changelog e Novas Funcionalidades

**Data de Lançamento:** Setembro 2025  
**Versão Anterior:** v2.0  
**Status:** ✅ Em Produção

---

## 📋 Resumo Executivo

A versão 2.5 do SIGESCON traz um conjunto robusto de novas funcionalidades focadas em **automação**, **configurabilidade** e **gestão inteligente de pendências**. As principais melhorias incluem:

- **Sistema de Configurações Dinâmicas** - Parâmetros ajustáveis sem alteração de código
- **Pendências Automáticas Configuráveis** - Criação inteligente baseada em período de contrato
- **Lembretes Dinâmicos** - Scheduler configurável com preview de impacto
- **Dashboard Administrativo Completo** - Métricas em tempo real e drill-down
- **Gestão Avançada de Pendências** - Separação entre vencidas e pendentes
- **Interface de Administração** - Página dedicada no frontend para configurações

---

## 🆕 Novas Funcionalidades

### 1. Sistema de Configurações (Backend)

#### **Arquivos Criados/Modificados:**
- ✅ `app/repositories/config_repo.py` - Repository para configurações
- ✅ `app/services/config_service.py` - Lógica de negócio
- ✅ `app/schemas/config_schema.py` - Schemas Pydantic
- ✅ `app/api/routers/config_router.py` - Endpoints REST

#### **Endpoints Implementados:**
```
GET    /api/v1/config/                              # Listar todas
GET    /api/v1/config/{chave}                        # Buscar específica
PATCH  /api/v1/config/{chave}                        # Atualizar
GET    /api/v1/config/pendencias/intervalo-dias     # Intervalo pendências
PATCH  /api/v1/config/pendencias/intervalo-dias     # Atualizar intervalo
GET    /api/v1/config/lembretes/config              # Config lembretes
PATCH  /api/v1/config/lembretes/config              # Atualizar lembretes
```

#### **Tabela no Banco:**
```sql
configuracao_sistema (
  id SERIAL PRIMARY KEY,
  chave VARCHAR UNIQUE,
  valor TEXT,
  descricao TEXT,
  tipo VARCHAR,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

#### **Configurações Disponíveis:**
1. **pendencias_automaticas_intervalo_dias** (1-365 dias)
   - Intervalo para criação automática de pendências
   - Padrão: 60 dias

2. **lembretes_dias_antes_vencimento_inicio** (1-90 dias)
   - Quantos dias antes do vencimento começar lembretes
   - Padrão: 30 dias

3. **lembretes_intervalo_dias** (1-30 dias)
   - Intervalo entre lembretes até vencimento
   - Padrão: 5 dias

---

### 2. Pendências Automáticas Configuráveis

#### **Arquivos Modificados:**
- ✅ `app/services/pendencia_automatica_service.py` - Lógica de criação
- ✅ `app/api/routers/contrato_router.py` - Novos endpoints

#### **Funcionalidades:**

**Preview de Pendências:**
```
POST /api/v1/contratos/{id}/pendencias-automaticas/preview
Body: { "intervalo_dias": 60 }
```
- Visualiza pendências que serão criadas
- Não cria nada no banco
- Retorna lista completa com datas calculadas

**Criação Efetiva:**
```
POST /api/v1/contratos/{id}/pendencias-automaticas/criar
Body: { "intervalo_dias": 60 }
```
- Cria todas as pendências calculadas
- Nomenclatura automática sequencial
- Envia emails aos fiscais
- Retorna resumo de criação

#### **Exemplo de Uso:**
```
Contrato: 01/10/2025 a 30/09/2026 (365 dias)
Intervalo: 60 dias

Pendências criadas:
1. "1º Relatório Fiscal" - Prazo: 30/11/2025 (60 dias após início)
2. "2º Relatório Fiscal" - Prazo: 29/01/2026 (120 dias após início)
3. "3º Relatório Fiscal" - Prazo: 30/03/2026 (180 dias após início)
4. "4º Relatório Fiscal" - Prazo: 29/05/2026 (240 dias após início)
5. "5º Relatório Fiscal" - Prazo: 28/07/2026 (300 dias após início)
6. "6º Relatório Fiscal" - Prazo: 26/09/2026 (360 dias após início)

Total: 6 pendências
```

---

### 3. Sistema de Lembretes Dinâmicos

#### **Arquivos Modificados:**
- ✅ `app/scheduler.py` - Scheduler com configurações dinâmicas
- ✅ `app/services/notification_service.py` - Notificações configuráveis

#### **Funcionamento:**

**Antes (Hardcoded):**
```python
dias_lembrete = [15, 5, 3, 0]  # Fixo no código
```

**Depois (Configurável):**
```python
# Busca do banco de dados
dias_antes_inicio = await config_repo.get_lembretes_dias_antes_inicio()  # 30
intervalo_dias = await config_repo.get_lembretes_intervalo_dias()  # 5

# Calcula dinamicamente
dias_lembrete = [30, 25, 20, 15, 10, 5, 0]  # Calculado automaticamente
```

#### **Logs Melhorados:**
```
📋 Configurações de lembretes: Início=30 dias antes, Intervalo=5 dias
📅 Lembretes serão enviados nos seguintes dias antes do vencimento: [30, 25, 20, 15, 10, 5, 0]
✅ Email enviado para João Fiscal - Pendência vence em 30 dia(s)
📧 Total de emails de lembrete enviados: 5
```

---

### 4. Dashboard Administrativo Completo

#### **Arquivos Criados/Modificados:**
- ✅ `app/api/routers/dashboard_router.py` - Endpoints expandidos
- ✅ `app/services/dashboard_service.py` - Lógica de dashboard
- ✅ `app/repositories/pendencia_repo.py` - Queries otimizadas

#### **Novos Endpoints:**

**Gestão de Pendências:**
```
GET /api/v1/dashboard/admin/pendencias-vencidas      # Vencidas com atraso
GET /api/v1/dashboard/admin/pendencias-pendentes     # Ainda não vencidas
PATCH /api/v1/dashboard/admin/cancelar-pendencia/{id} # Cancelar
```

**Alertas de Contratos:**
```
GET /api/v1/dashboard/admin/contratos-proximos-vencimento
Query: dias_antecedencia=90 (30-365)
```

**Relatórios para Análise:**
```
GET /api/v1/dashboard/admin/relatorios-pendentes-analise
```

**Dashboard Melhorado:**
```
GET /api/v1/dashboard/admin/melhorado
```

#### **Métricas Disponíveis:**
- Total de contratos / Contratos ativos
- Total de usuários por perfil
- Total de pendências / Vencidas / Aguardando análise
- Relatórios pendentes de análise
- Contratos próximos ao vencimento (30/60/90 dias)
- Drill-down para cada métrica

---

### 5. Interface de Administração (Frontend)

#### **Arquivos Criados:**
- ✅ `sigescon/src/pages/admin/Administracao.tsx` - Página completa

#### **Funcionalidades da Interface:**

**Card 1: Pendências Automáticas**
- Input: Intervalo em dias (1-365)
- Validação em tempo real
- Preview do número de pendências
- Botões: Salvar / Resetar
- Feedback visual de alterações não salvas

**Card 2: Lembretes de Pendências** (NOVO)
- Input 1: Dias antes do vencimento (1-90)
- Input 2: Intervalo entre lembretes (1-30)
- **Preview dinâmico:** Mostra quantos lembretes serão enviados
- **Exemplo em tempo real:** "Com 30 dias antes e intervalo de 5 dias, serão enviados aproximadamente 7 lembretes por pendência"
- Cores temáticas: Âmbar/Laranja
- Ícone: Sino (Bell)

**Card 3: Informações**
- Explicação da nomenclatura automática
- Detalhes sobre notificações por email
- Como as configurações são aplicadas

#### **Componentes Reutilizáveis:**
- Card, CardHeader, CardContent
- Input com validação
- Button com estados (loading, disabled)
- Toast notifications

---

### 6. Página de Gestão de Pendências

#### **Arquivos Modificados:**
- ✅ `sigescon/src/pages/admin/PendenciasVencidas.tsx` - Renomeado para GestãoPendências

#### **Melhorias:**
- **Separação Visual:** Vencidas (vermelho) vs Pendentes (laranja)
- **Filtros Aprimorados:** Contrato, Status, Fiscal, Tipo
- **Cards Informativos:** Quantidade total de cada tipo
- **Rota Melhorada:** `/gestao-de-pendencias` (mantém compatibilidade com `/pendencias-vencidas`)

---

### 7. API do Frontend

#### **Arquivos Modificados:**
- ✅ `sigescon/src/lib/api.ts` - Novas funções

#### **Funções Implementadas:**

```typescript
// Configurações de pendências automáticas
getPendenciasIntervaloDias(): Promise<{ intervalo_dias: number }>
updatePendenciasIntervaloDias(intervalo_dias: number): Promise<ConfiguracaoSistema>

// Configurações de lembretes (NOVO)
getLembretesConfig(): Promise<{
  dias_antes_vencimento_inicio: number,
  intervalo_dias_lembrete: number
}>

updateLembretesConfig(
  dias_antes_vencimento_inicio: number,
  intervalo_dias_lembrete: number
): Promise<{...}>

// Dashboard administrativo
getDashboardAdminCompleto(): Promise<DashboardAdminResponse>
getDashboardAdminPendenciasVencidas(limit?: number): Promise<{...}>
getDashboardAdminPendenciasPendentes(limit?: number): Promise<{...}>

// Pendências automáticas
previewPendenciasAutomaticas(contrato_id: number, intervalo?: number): Promise<{...}>
criarPendenciasAutomaticas(contrato_id: number, intervalo?: number): Promise<{...}>
```

---

## 🔧 Melhorias Técnicas

### Backend:

1. **Configurações no Banco de Dados**
   - Não mais hardcoded
   - Fácil manutenção
   - Auditoria de alterações

2. **Scheduler Inteligente**
   - Lê configurações a cada execução
   - Logs detalhados
   - Tratamento robusto de erros

3. **Queries Otimizadas**
   - JOINs eficientes
   - Índices apropriados
   - Paginação em todas as listagens

4. **Validações Robustas**
   - Backend valida ranges
   - Frontend mostra feedback imediato
   - Mensagens de erro claras

### Frontend:

1. **Componentização**
   - Cards reutilizáveis
   - Hooks personalizados
   - Separação de responsabilidades

2. **Estado Gerenciado**
   - useState para valores
   - useEffect para carregamento
   - Controle de loading/salvando

3. **UX Melhorada**
   - Preview em tempo real
   - Feedback visual instantâneo
   - Loading states apropriados
   - Toasts informativos

4. **Validações no Cliente**
   - Ranges de valores
   - Mensagens de erro contextuais
   - Desabilita botões quando necessário

---

## 📊 Impacto das Mudanças

### Para Administradores:
✅ Configuração visual sem precisar de acesso ao servidor  
✅ Preview de impacto antes de aplicar mudanças  
✅ Gestão centralizada de pendências  
✅ Dashboard com métricas em tempo real  
✅ Flexibilidade para ajustar conforme necessidade  

### Para Fiscais:
✅ Recebem lembretes em intervalos mais apropriados  
✅ Notificações claras quando pendências são criadas  
✅ Menos emails (configurável)  
✅ Melhor organização de prazos  

### Para o Sistema:
✅ Configurações persistidas no banco  
✅ Auditoria completa de alterações  
✅ Logs detalhados para debugging  
✅ Escalabilidade mantida  
✅ Performance otimizada  

---

## 🗄️ Migrações de Banco de Dados

### Script SQL Necessário:
```bash
migrations/add_lembretes_config.sql
```

### Execução:
```bash
psql -U postgres -d contratos -f migrations/add_lembretes_config.sql
```

### Verificação:
```sql
SELECT * FROM configuracao_sistema 
WHERE chave LIKE 'lembretes%' OR chave LIKE 'pendencias%'
ORDER BY chave;
```

---

## 📝 Documentação Atualizada

### Arquivos Atualizados:
1. ✅ `CLAUDE.md` - Documentação principal do projeto
2. ✅ `docs/Documentação da API SIGESCON v2.5 - Guia de Uso.md` - Guia completo
3. ✅ `LEMBRETES_PENDENCIAS.md` - Documentação específica dos lembretes
4. ✅ `CHANGELOG_v2.5.md` - Este arquivo

### Arquivos Criados:
- `migrations/add_lembretes_config.sql` - Script de migração
- `LEMBRETES_PENDENCIAS.md` - Documentação técnica completa

---

## 🧪 Testes Recomendados

### Backend:
1. **Configurações:**
   - [ ] Criar configuração nova
   - [ ] Atualizar configuração existente
   - [ ] Buscar configuração por chave
   - [ ] Validar ranges de valores

2. **Pendências Automáticas:**
   - [ ] Preview com diferentes intervalos
   - [ ] Criação efetiva
   - [ ] Emails enviados corretamente
   - [ ] Nomenclatura sequencial

3. **Lembretes:**
   - [ ] Scheduler lê configurações corretas
   - [ ] Dias calculados dinamicamente
   - [ ] Emails enviados nos dias certos
   - [ ] Logs informativos

4. **Dashboard:**
   - [ ] Métricas corretas
   - [ ] Filtros funcionando
   - [ ] Paginação adequada
   - [ ] Performance aceitável

### Frontend:
1. **Página de Administração:**
   - [ ] Carrega valores atuais
   - [ ] Validações funcionam
   - [ ] Preview atualiza em tempo real
   - [ ] Salva corretamente
   - [ ] Feedback visual apropriado

2. **Gestão de Pendências:**
   - [ ] Separação vencidas/pendentes
   - [ ] Filtros funcionam
   - [ ] Cards mostram dados corretos
   - [ ] Navegação funciona

---

## 🚀 Deploy

### Checklist de Deploy:

1. **Backend:**
   - [ ] Pull do código atualizado
   - [ ] Executar script SQL de migração
   - [ ] Verificar configurações criadas
   - [ ] Reiniciar serviço
   - [ ] Testar endpoints novos

2. **Frontend:**
   - [ ] Build da aplicação
   - [ ] Deploy dos arquivos estáticos
   - [ ] Limpar cache do navegador
   - [ ] Testar páginas novas

3. **Verificação:**
   - [ ] Acessar /administracao
   - [ ] Configurar lembretes
   - [ ] Criar pendências automáticas
   - [ ] Verificar dashboard
   - [ ] Confirmar emails

---

## 🎯 Próximos Passos (Opcional)

### Funcionalidades Futuras:
- [ ] Histórico de alterações de configurações
- [ ] Notificações também para substitutos
- [ ] Templates personalizáveis de email
- [ ] Relatório de efetividade dos lembretes
- [ ] Configuração de horário de envio
- [ ] Dashboard para gestor
- [ ] Exportação de métricas

### Melhorias Técnicas:
- [ ] Cache de configurações
- [ ] Testes automatizados
- [ ] Monitoramento de scheduler
- [ ] Alertas de falhas
- [ ] Backup automático de configurações

---

## 📞 Suporte

### Documentação:
- **CLAUDE.md** - Visão geral completa
- **Guia de Uso da API** - Endpoints detalhados
- **LEMBRETES_PENDENCIAS.md** - Funcionamento dos lembretes
- **Swagger UI** - http://localhost:8000/docs

### Logs:
- **Scheduler:** Logs detalhados de execução
- **Config:** Logs de leitura/escrita
- **Emails:** Confirmação de envios

---

**Versão:** 2.5  
**Data:** 30/09/2025  
**Status:** ✅ Em Produção  
**Mantido por:** Equipe SIGESCON  

*Este changelog documenta todas as mudanças significativas da versão 2.5. Para mais detalhes, consulte a documentação completa.*
