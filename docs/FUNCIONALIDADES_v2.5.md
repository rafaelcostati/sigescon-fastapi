# 🌟 Guia de Funcionalidades v2.5 - SIGESCON

**Versão:** 2.5  
**Data:** Setembro 2025  
**Público:** Administradores e Usuários Finais

---

## 📖 Índice

1. [Visão Geral](#visão-geral)
2. [Para Administradores](#para-administradores)
3. [Para Fiscais](#para-fiscais)
4. [Para Gestores](#para-gestores)
5. [Perguntas Frequentes](#perguntas-frequentes)

---

## 🎯 Visão Geral

A versão 2.5 do SIGESCON introduz funcionalidades que tornam o sistema **mais inteligente**, **configurável** e **automatizado**. As principais novidades são:

### O que há de novo?

1. **🔧 Configurações do Sistema** - Ajuste parâmetros sem acesso ao código
2. **📋 Pendências Automáticas** - Criação inteligente baseada em período
3. **🔔 Lembretes Configuráveis** - Defina quando e com que frequência lembrar
4. **📊 Dashboard Melhorado** - Métricas em tempo real e gestão de pendências
5. **⚡ Interface de Administração** - Página dedicada para configurações

---

## 👨‍💼 Para Administradores

### 1. Página de Administração

**Como acessar:**
- Menu lateral → **Administração**
- URL: `/administracao`

**O que você pode fazer:**

#### 📋 Configurar Pendências Automáticas

**Para que serve:** Define com que frequência o sistema criará pendências automáticas de relatórios fiscais.

**Como configurar:**
1. Acesse a página de Administração
2. Localize o card "Pendências Automáticas"
3. Digite o intervalo desejado (1-365 dias)
4. Visualize o preview: "Um contrato de 1 ano gerará X pendências"
5. Clique em "Salvar Configuração"

**Exemplo prático:**
- **Intervalo: 60 dias**
- Contrato: 01/01/2025 a 31/12/2025 (365 dias)
- **Resultado:** 6 pendências criadas automaticamente:
  - 1º Relatório Fiscal - 02/03/2025
  - 2º Relatório Fiscal - 01/05/2025
  - 3º Relatório Fiscal - 30/06/2025
  - 4º Relatório Fiscal - 29/08/2025
  - 5º Relatório Fiscal - 28/10/2025
  - 6º Relatório Fiscal - 27/12/2025

#### 🔔 Configurar Lembretes

**Para que serve:** Define quando o sistema começará a enviar lembretes aos fiscais e com que frequência.

**Como configurar:**
1. Acesse a página de Administração
2. Localize o card "Lembretes de Pendências"
3. Configure dois valores:
   - **Início dos Lembretes:** Quantos dias antes do vencimento começar (1-90 dias)
   - **Intervalo entre Lembretes:** A cada quantos dias repetir (1-30 dias)
4. Veja o preview: "Serão enviados aproximadamente X lembretes"
5. Clique em "Salvar Configuração"

**Exemplo prático:**
- **Início:** 30 dias antes do vencimento
- **Intervalo:** 5 dias
- **Resultado:** Fiscal receberá lembretes:
  - 30 dias antes
  - 25 dias antes
  - 20 dias antes
  - 15 dias antes
  - 10 dias antes
  - 5 dias antes
  - No dia do vencimento
  - **Total:** 7 lembretes por pendência

**💡 Dicas:**
- Intervalos maiores = Menos emails, mais espaçados
- Intervalos menores = Mais lembretes, fiscais mais alertados
- Recomendado: 30 dias antes, intervalo de 5-7 dias

---

### 2. Criar Pendências Automáticas

**Como funciona:**

1. **Acesse um contrato** (qualquer contrato ativo)
2. **Menu de ações (3 pontos)** → Criar Pendências Automáticas
3. **Visualize o preview:**
   - Sistema mostra todas as pendências que serão criadas
   - Datas calculadas automaticamente
   - Nomenclatura sequencial
4. **Confirme a criação**
5. **Resultado:**
   - Pendências criadas no sistema
   - Fiscal recebe email com lista completa
   - Fiscal substituto também recebe (se houver)

**Email enviado ao fiscal:**
```
Assunto: Pendências Criadas - Contrato CT-2025-001

Olá João Silva,

Foram criadas 6 pendências automáticas para o contrato "Manutenção de Software":

1. 1º Relatório Fiscal - Prazo: 02/03/2025
2. 2º Relatório Fiscal - Prazo: 01/05/2025
3. 3º Relatório Fiscal - Prazo: 30/06/2025
4. 4º Relatório Fiscal - Prazo: 29/08/2025
5. 5º Relatório Fiscal - Prazo: 28/10/2025
6. 6º Relatório Fiscal - Prazo: 27/12/2025

Por favor, fique atento aos prazos.
```

---

### 3. Dashboard Administrativo

**Novidades:**

#### 📊 Métricas em Tempo Real
- Total de contratos / Contratos ativos
- Total de usuários por perfil
- Pendências vencidas
- Pendências pendentes
- Relatórios aguardando análise
- Contratos próximos ao vencimento

#### 🚨 Alertas de Vencimento
- Contratos que vencem em 30 dias
- Contratos que vencem em 60 dias
- Contratos que vencem em 90 dias
- Clique para ver detalhes

#### 📋 Gestão de Pendências
**Acesso:** Menu lateral → **Gestão de Pendências**

**Pendências Vencidas (Urgente - Vermelho):**
- Lista todas as pendências com prazo expirado
- Mostra dias de atraso
- Filtros: Contrato, Fiscal, Status
- Ações: Visualizar contrato, Cancelar pendência

**Pendências Pendentes (Atenção - Laranja):**
- Lista pendências ainda não vencidas
- Mostra dias restantes
- Acompanhamento preventivo
- Filtros disponíveis

---

### 4. Fluxo Completo de Uso

**Cenário:** Novo contrato de 1 ano

**Passo 1: Configure o sistema**
1. Acesse Administração
2. Configure: Intervalo de 60 dias
3. Configure lembretes: 30 dias antes, intervalo de 5 dias

**Passo 2: Crie o contrato**
1. Vá para Contratos → Novo Contrato
2. Preencha os dados
3. Associe fiscal e gestor
4. Salve

**Passo 3: Crie pendências automáticas**
1. No contrato criado, clique nos 3 pontos
2. "Criar Pendências Automáticas"
3. Visualize preview (6 pendências)
4. Confirme

**Passo 4: Sistema trabalha sozinho**
- ✅ Pendências criadas
- ✅ Fiscais notificados por email
- ✅ Scheduler enviará lembretes automaticamente
- ✅ Dashboard atualizado em tempo real

**Passo 5: Monitore via Dashboard**
1. Acompanhe pendências vencidas
2. Verifique relatórios pendentes de análise
3. Analise relatórios conforme chegam
4. Aprove/Rejeite com feedback

---

## 👷 Para Fiscais

### O que muda para você?

#### 📧 Lembretes Mais Inteligentes

**Antes:**
- Recebia lembretes em dias fixos (15, 7, 3, 1 dias antes)
- Sem flexibilidade

**Agora:**
- Administrador configura quando você receberá lembretes
- Intervalos personalizados
- Exemplo: 30, 25, 20, 15, 10, 5 dias antes e no vencimento

#### 📋 Notificação de Pendências Criadas

Quando o administrador criar pendências automáticas:
- ✅ Você recebe email com lista completa
- ✅ Todas as datas de prazo
- ✅ Nomenclatura clara (1º, 2º, 3º Relatório)

#### 📊 Dashboard Melhorado

**Acesso:** Menu lateral → **Dashboard**

**Você vê:**
- Suas pendências ordenadas por prazo
- Dias restantes para cada uma
- Status de cada pendência
- Contratos associados

---

## 👔 Para Gestores

### O que muda para você?

#### 📊 Visão Mais Clara

**Dashboard do Gestor:**
- Contratos sob sua gestão
- Pendências de seus contratos
- Status dos relatórios
- Fiscais associados

#### 📋 Acompanhamento

- Veja quais fiscais estão com pendências
- Identifique relatórios pendentes de análise
- Monitore prazos

---

## ❓ Perguntas Frequentes

### Para Administradores:

**P: Posso mudar as configurações a qualquer momento?**  
R: Sim! As configurações são aplicadas a partir do momento que você salva. Pendências já criadas não são afetadas, mas novas pendências e lembretes seguirão as novas regras.

**P: O que acontece se eu criar pendências automáticas duas vezes no mesmo contrato?**  
R: O sistema permite criar, mas você terá pendências duplicadas. Recomendamos criar apenas uma vez por contrato.

**P: Posso cancelar pendências criadas automaticamente?**  
R: Sim! Vá para Gestão de Pendências, localize a pendência e clique em "Cancelar". O fiscal receberá email informando.

**P: Como sei se os lembretes estão sendo enviados?**  
R: O sistema mantém logs de todos os emails enviados. Entre em contato com o suporte técnico para verificar.

**P: Posso ter configurações diferentes para contratos diferentes?**  
R: Não na versão 2.5. As configurações são globais. Mas você pode criar pendências com intervalos personalizados usando o preview.

### Para Fiscais:

**P: Vou receber muitos emails?**  
R: Depende da configuração do administrador. Exemplo: com 30 dias antes e intervalo de 5 dias, você receberá 7 lembretes por pendência.

**P: Posso desativar os lembretes?**  
R: Não. Os lembretes são parte do sistema de controle. Entre em contato com seu gestor ou administrador se achar excessivo.

**P: O que fazer quando receber a notificação de pendências criadas?**  
R: Anote as datas de prazo em sua agenda. O sistema enviará lembretes conforme a data se aproximar.

**P: Posso ver todas as pendências futuras?**  
R: Sim! Acesse seu dashboard ou a página "Minhas Pendências". Todas as pendências, inclusive futuras, estão listadas.

### Para Gestores:

**P: Posso criar pendências?**  
R: Não. Apenas administradores podem criar pendências (manuais ou automáticas).

**P: Posso alterar as configurações de lembretes?**  
R: Não. Apenas administradores têm acesso à página de configurações.

**P: Como acompanhar o progresso dos fiscais?**  
R: Use o dashboard do gestor para ver pendências dos contratos sob sua gestão.

---

## 🎓 Tutoriais Rápidos

### Tutorial 1: Configurar Sistema pela Primeira Vez

1. **Login como Admin**
2. **Menu → Administração**
3. **Card "Pendências Automáticas":**
   - Digite: 60 dias
   - Clique: Salvar
4. **Card "Lembretes":**
   - Dias antes: 30
   - Intervalo: 5
   - Clique: Salvar
5. **Pronto!** Sistema configurado

### Tutorial 2: Criar Primeiro Contrato com Pendências Automáticas

1. **Menu → Contratos → Novo Contrato**
2. **Preencha todos os campos obrigatórios**
3. **Associe Fiscal e Gestor**
4. **Salve o contrato**
5. **No contrato salvo: 3 pontos → Criar Pendências Automáticas**
6. **Visualize o preview**
7. **Confirme**
8. **Verifique o email do fiscal**

### Tutorial 3: Monitorar Pendências Vencidas

1. **Menu → Gestão de Pendências**
2. **Seção "Pendências Vencidas" (vermelho)**
3. **Veja lista com dias de atraso**
4. **Use filtros se necessário:**
   - Por contrato
   - Por fiscal
   - Por status
5. **Clique em um card para ver detalhes**
6. **Ações disponíveis:**
   - Ver contrato completo
   - Cancelar pendência (se necessário)

---

## 📱 Interface Responsiva

Todas as novas funcionalidades funcionam em:
- 💻 Desktop
- 📱 Tablet
- 📱 Smartphone

---

## 🆘 Suporte

**Problemas técnicos:**
- Acesse a documentação completa em `/docs`
- Swagger UI: http://localhost:8000/docs
- Entre em contato com o suporte técnico

**Dúvidas sobre uso:**
- Consulte este guia
- Entre em contato com o administrador do sistema
- Treinamentos disponíveis sob demanda

---

## 🔄 Atualizações Futuras

**Em desenvolvimento:**
- Histórico de alterações de configurações
- Templates personalizáveis de email
- Relatórios de efetividade de lembretes
- Dashboard para gestores expandido
- Exportação de métricas

---

**Versão do Documento:** 1.0  
**Última Atualização:** 30/09/2025  
**Feedback:** Entre em contato com a equipe de desenvolvimento

---

*Este guia foi criado para ajudar todos os usuários a aproveitar ao máximo as novas funcionalidades do SIGESCON v2.5. Para documentação técnica detalhada, consulte os outros documentos na pasta `/docs`.*
