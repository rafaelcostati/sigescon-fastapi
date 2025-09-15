# 🚀 Guia de Análise e Desenvolvimento do Projeto SIGESCON-FastAPI

## 1. Visão Geral do Projeto

**SIGESCON** (Sistema de Gestão de Contratos) é uma API back-end projetada para gerenciar o ciclo de vida de contratos governamentais ou corporativos. O projeto original foi desenvolvido com Flask (`py-back-contratos`) e está em processo de migração para FastAPI (`sigescon-fastapi`) para aproveitar os benefícios de performance, código assíncrono, tipagem estrita e documentação automática.

**Core Business:**
- Gerenciar Contratos, Contratados, Usuários e tabelas de apoio (Modalidades, Status).
- Orquestrar um fluxo de trabalho de fiscalização: um **Administrador** cria uma **Pendência** para um **Fiscal**, que por sua vez submete um **Relatório** (com anexo). O Administrador então aprova ou rejeita este relatório.
- Um **Gestor** tem visão de alto nível sobre os contratos pelos quais é responsável.

---

## 2. Arquitetura e Princípios de Design

O projeto segue uma arquitetura em camadas (multi-tier) para garantir a separação de responsabilidades, testabilidade e manutenibilidade.