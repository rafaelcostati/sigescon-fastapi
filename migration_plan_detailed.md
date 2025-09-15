# 📋 Plano de Migração SIGESCON: Flask → FastAPI

## Status Atual da Migração

### ✅ Fase 1: Módulo de Usuários - CONCLUÍDO
- [x] Repository completo com todas as operações
- [x] Schemas com validação de CPF
- [x] Service com lógica de negócio
- [x] Router com todos os endpoints
- [x] Sistema de permissões básico
- [x] Testes automatizados abrangentes

### 🚀 Próximos Passos Imediatos

## Fase 2: Sistema de Permissões Robusto (2-3 dias)

### 2.1 Criar Decoradores de Permissão
```python
# app/api/permissions.py
- admin_required()
- fiscal_required()
- gestor_required()
- owner_or_admin() # Para recursos próprios
```

### 2.2 Implementar Middleware de Logging
```python
# app/middleware/logging.py
- Request/Response logging
- Audit trail para ações críticas
- Performance monitoring
```

### 2.3 Exception Handlers Globais
```python
# app/api/exceptions.py
- ValidationException
- BusinessRuleException
- PermissionDeniedException
- ResourceNotFoundException
```

## Fase 3: Tabelas Auxiliares (3-4 dias)

### 3.1 Perfis
- [ ] Schema: PerfilBase, PerfilCreate, Perfil
- [ ] Repository: PerfilRepository
- [ ] Service: PerfilService
- [ ] Router: GET /perfis
- [ ] Testes

### 3.2 Modalidades
- [ ] Schema com validações
- [ ] Repository assíncrono
- [ ] Service com regras de negócio
- [ ] Router com CRUD completo
- [ ] Testes de integração

### 3.3 Status
- [ ] Schemas para Status de Contrato
- [ ] Repository com soft delete
- [ ] Service com verificação de uso
- [ ] Router protegido
- [ ] Testes

### 3.4 Status de Relatório e Pendência
- [ ] Schemas específicos
- [ ] Repositories
- [ ] Services
- [ ] Routers
- [ ] Testes

## Fase 4: Módulo de Contratos (5-7 dias)

### 4.1 Upload de Arquivos
```python
# app/services/file_service.py
- Validação de tipos permitidos
- Geração de hash único
- Armazenamento seguro
- Streaming para arquivos grandes
```

### 4.2 Schema de Contratos
```python
# app/schemas/contrato_schema.py
- ContratoBase
- ContratoCreate (com arquivos)
- ContratoUpdate
- ContratoFilter (para buscas)
- ContratoPaginated (resposta paginada)
```

### 4.3 Repository de Contratos
- [ ] Queries complexas com JOINs
- [ ] Filtros avançados
- [ ] Paginação eficiente
- [ ] Agregações para dashboard

### 4.4 Service de Contratos
- [ ] Criação com notificação por email
- [ ] Validações de negócio
- [ ] Gerenciamento de arquivos
- [ ] Histórico de alterações

### 4.5 Router de Contratos
- [ ] POST /contratos (com multipart/form-data)
- [ ] GET /contratos (com filtros e paginação)
- [ ] GET /contratos/{id}
- [ ] PATCH /contratos/{id}
- [ ] DELETE /contratos/{id}
- [ ] GET /contratos/{id}/arquivos

## Fase 5: Relatórios e Pendências (4-5 dias)

### 5.1 Pendências
- [ ] Schema com validação de datas
- [ ] Repository com queries relacionais
- [ ] Service com notificações
- [ ] Router aninhado: /contratos/{id}/pendencias

### 5.2 Relatórios Fiscais
- [ ] Schema com estados do workflow
- [ ] Repository com histórico
- [ ] Service com fluxo de aprovação
- [ ] Router com upload de arquivos
- [ ] Reenvio de correções

## Fase 6: Funcionalidades Avançadas (3-4 dias)

### 6.1 Sistema de Email
```python
# app/services/email_service.py
- Templates HTML
- Queue assíncrona
- Retry mechanism
- Tracking de envios
```

### 6.2 Scheduler de Lembretes
```python
# app/scheduler/tasks.py
- APScheduler ou Celery
- Verificação de prazos
- Envio de notificações
- Relatórios periódicos
```

### 6.3 Sistema de Cache
```python
# app/core/cache.py
- Redis para cache
- Invalidação inteligente
- Cache de queries pesadas
```

## Fase 7: Otimizações e Melhorias (2-3 dias)

### 7.1 Performance
- [ ] Índices no banco de dados
- [ ] Query optimization
- [ ] Connection pooling otimizado
- [ ] Lazy loading onde aplicável

### 7.2 Segurança
- [ ] Rate limiting
- [ ] CORS configurado
- [ ] SQL injection prevention (já coberto pelo asyncpg)
- [ ] Input sanitization

### 7.3 Documentação
- [ ] Swagger customizado com exemplos
- [ ] README atualizado
- [ ] Guia de deployment
- [ ] API versioning strategy

## Fase 8: Testes e Validação Final (2-3 dias)

### 8.1 Testes de Integração
- [ ] Fluxo completo de contrato
- [ ] Workflow de relatórios
- [ ] Cenários de erro
- [ ] Testes de carga

### 8.2 Comparação com Flask
- [ ] Validar todas as rotas
- [ ] Verificar responses
- [ ] Testar compatibilidade
- [ ] Migration script para dados

## 📊 Estimativa Total: 25-35 dias

## 🎯 Critérios de Sucesso

1. **Funcionalidade**: 100% de paridade com o sistema Flask
2. **Performance**: Melhoria de 30% no tempo de resposta
3. **Testes**: Cobertura mínima de 80%
4. **Documentação**: Swagger completo e atualizado
5. **Segurança**: Todas as rotas protegidas adequadamente

## 🔄 Processo de Desenvolvimento

Para cada módulo:
1. **Design**: Definir schemas e interfaces
2. **Implement**: Repository → Service → Router
3. **Test**: Unit tests → Integration tests
4. **Document**: Docstrings e Swagger
5. **Review**: Code review e refactoring

## 📝 Convenções de Código

### Naming
- **Schemas**: PascalCase (UsuarioCreate)
- **Funções**: snake_case (get_user_by_id)
- **Constantes**: UPPER_CASE (MAX_FILE_SIZE)

### Estrutura
```
app/
├── api/
│   ├── routers/     # Endpoints
│   ├── dependencies/ # Injeção de dependências
│   └── middleware/   # Middlewares
├── core/            # Configurações core
├── schemas/         # Modelos Pydantic
├── services/        # Lógica de negócio
├── repositories/    # Acesso a dados
└── utils/          # Funções auxiliares
```

### Git Workflow
- Branch principal: `main`
- Feature branches: `feature/module-name`
- Commits semânticos: `feat:`, `fix:`, `docs:`, `test:`
- Pull requests com testes passando

## 🚨 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Incompatibilidade de dados | Média | Alto | Scripts de migração e validação |
| Performance degradada | Baixa | Médio | Profiling e otimização contínua |
| Bugs em produção | Média | Alto | Testes abrangentes e staging env |
| Atraso no cronograma | Média | Médio | Priorização e entregas incrementais |

## 📅 Próximas Ações Imediatas

1. **Hoje**: Implementar sistema de permissões
2. **Amanhã**: Começar módulo de Perfis
3. **Esta semana**: Completar todas as tabelas auxiliares
4. **Próxima semana**: Iniciar módulo de Contratos

---

**Última atualização**: Dezembro 2024
**Responsável**: Equipe de Desenvolvimento
**Status**: 🟡 Em Progresso