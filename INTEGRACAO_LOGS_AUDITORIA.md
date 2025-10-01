# Integração de Logs de Auditoria nos Services

Este documento explica como integrar os logs de auditoria nos services existentes do sistema.

## 📋 Visão Geral

O sistema de auditoria foi criado para rastrear automaticamente todas as ações importantes realizadas pelos usuários no sistema.

### Estrutura criada:
- ✅ **Tabela**: `audit_log` no banco de dados
- ✅ **Repository**: `AuditLogRepository`
- ✅ **Service**: `AuditLogService`
- ✅ **Helpers**: `audit_integration.py` com funções prontas
- ✅ **Router**: Endpoints para consulta de logs

## 🔧 Como Integrar

### 1. Importar o helper de integração

```python
from app.services.audit_integration import (
    audit_criar_contrato,
    audit_atualizar_contrato,
    audit_criar_pendencia,
    audit_atualizar_pendencia,
    audit_criar_pendencias_automaticas,
    audit_atualizar_configuracao,
    audit_aprovar_relatorio,
    audit_rejeitar_relatorio
)
```

### 2. Exemplo: Integrar no ContratoService

#### Método `create_contrato`

**Localização**: `app/services/contrato_service.py` linha ~131

**Adicionar APÓS criar o contrato e ANTES do return:**

```python
async def create_contrato(
    self,
    contrato_create: ContratoCreate,
    files: Optional[List[UploadFile]] = None,
    current_user: Optional[Usuario] = None,  # ← ADICIONAR PARÂMETRO
    request: Optional[Request] = None  # ← ADICIONAR PARÂMETRO
) -> Contrato:
    # ... código existente ...

    # Cria o contrato
    new_contrato_data = await self.contrato_repo.create_contrato(contrato_create)
    contrato_id = new_contrato_data['id']

    # ... processamento de arquivos ...

    # ✅ ADICIONAR LOG DE AUDITORIA
    if current_user:
        try:
            await audit_criar_contrato(
                conn=self.contrato_repo.conn,
                request=request,
                usuario=current_user,
                contrato_id=contrato_id,
                dados_contrato={
                    'nr_contrato': contrato_create.nr_contrato,
                    'objeto': contrato_create.objeto,
                    'contratado_id': contrato_create.contratado_id,
                    'gestor_id': contrato_create.gestor_id,
                    'fiscal_id': contrato_create.fiscal_id,
                    'valor_global': str(contrato_create.valor_global) if contrato_create.valor_global else None,
                    'data_inicio': str(contrato_create.data_inicio),
                    'data_fim': str(contrato_create.data_fim)
                },
                perfil_usado=current_user.perfil_ativo if hasattr(current_user, 'perfil_ativo') else None
            )
        except Exception as e:
            # Log, mas não falha a criação
            logger.warning(f"Erro ao criar log de auditoria: {e}")

    return contrato_response
```

#### Método `update_contrato`

**Adicionar APÓS atualizar o contrato:**

```python
async def update_contrato(
    self,
    contrato_id: int,
    contrato_update: ContratoUpdate,
    documento_contrato: Optional[List[UploadFile]] = None,
    current_user: Optional[Usuario] = None,  # ← ADICIONAR
    request: Optional[Request] = None  # ← ADICIONAR
) -> Optional[Contrato]:
    # ... código existente ...

    # Busca dados anteriores
    existing_contrato = await self.contrato_repo.find_contrato_by_id(contrato_id)

    # Atualiza o contrato
    updated_data = await self.contrato_repo.update_contrato(contrato_id, contrato_update)

    # ✅ ADICIONAR LOG DE AUDITORIA
    if current_user and existing_contrato:
        try:
            # Preparar dados anteriores
            dados_anteriores = {
                'objeto': existing_contrato.get('objeto'),
                'valor_global': str(existing_contrato.get('valor_global')) if existing_contrato.get('valor_global') else None,
                'gestor_id': existing_contrato.get('gestor_id'),
                'fiscal_id': existing_contrato.get('fiscal_id')
            }

            # Preparar dados novos
            dados_novos = {}
            if contrato_update.objeto:
                dados_novos['objeto'] = contrato_update.objeto
            if contrato_update.valor_global:
                dados_novos['valor_global'] = str(contrato_update.valor_global)
            if contrato_update.gestor_id:
                dados_novos['gestor_id'] = contrato_update.gestor_id
            if contrato_update.fiscal_id:
                dados_novos['fiscal_id'] = contrato_update.fiscal_id

            await audit_atualizar_contrato(
                conn=self.contrato_repo.conn,
                request=request,
                usuario=current_user,
                contrato_id=contrato_id,
                nr_contrato=existing_contrato['nr_contrato'],
                dados_anteriores=dados_anteriores,
                dados_novos=dados_novos,
                perfil_usado=current_user.perfil_ativo if hasattr(current_user, 'perfil_ativo') else None
            )
        except Exception as e:
            logger.warning(f"Erro ao criar log de auditoria: {e}")

    return updated_contrato
```

### 3. Exemplo: Integrar no Router

**Os routers precisam passar `current_user` e `request` para os services:**

```python
# app/api/routers/contrato_router.py

@router.post("/", response_model=Contrato)
async def create_contrato(
    request: Request,  # ← ADICIONAR
    # ... outros parâmetros ...
    service: ContratoService = Depends(get_contrato_service),
    current_user: Usuario = Depends(admin_required)  # ← USAR
):
    """Cria um novo contrato"""

    contrato_create = ContratoCreate(...)

    # Passar current_user e request para o service
    return await service.create_contrato(
        contrato_create,
        documento_contrato,
        current_user=current_user,  # ← PASSAR
        request=request  # ← PASSAR
    )
```

### 4. Exemplo: Pendências

```python
# No PendenciaService

async def criar_pendencia(
    self,
    pendencia_data: PendenciaCreate,
    current_user: Usuario,
    request: Request
):
    # Cria a pendência
    nova_pendencia = await self.pendencia_repo.create_pendencia(pendencia_data)

    # Busca dados do contrato
    contrato = await self.contrato_repo.find_contrato_by_id(pendencia_data.contrato_id)

    # ✅ LOG DE AUDITORIA
    if current_user:
        try:
            await audit_criar_pendencia(
                conn=self.pendencia_repo.conn,
                request=request,
                usuario=current_user,
                pendencia_id=nova_pendencia['id'],
                titulo_pendencia=pendencia_data.titulo,
                contrato_nr=contrato['nr_contrato']
            )
        except Exception as e:
            logger.warning(f"Erro ao criar log: {e}")

    return nova_pendencia
```

### 5. Exemplo: Configurações

```python
# No ConfigService

async def update_pendencias_intervalo_dias(
    self,
    intervalo_dias: int,
    current_user: Usuario,
    request: Request
) -> Config:
    # Busca valor anterior
    config_anterior = await self.config_repo.get_pendencias_intervalo_dias()

    # Atualiza
    updated = await self.config_repo.update_config('pendencias_automaticas_intervalo_dias', str(intervalo_dias))

    # ✅ LOG DE AUDITORIA
    if current_user:
        try:
            await audit_atualizar_configuracao(
                conn=self.config_repo.conn,
                request=request,
                usuario=current_user,
                chave_config='pendencias_automaticas_intervalo_dias',
                valor_anterior=config_anterior,
                valor_novo=intervalo_dias
            )
        except Exception as e:
            logger.warning(f"Erro ao criar log: {e}")

    return updated
```

## 📌 Checklist de Integração

### ContratoService
- [ ] `create_contrato()` - Adicionar log de criação
- [ ] `update_contrato()` - Adicionar log de atualização
- [ ] `delete_contrato()` - Adicionar log de deleção (se existir)

### PendenciaService
- [ ] `criar_pendencia()` - Adicionar log de criação
- [ ] `atualizar_status_pendencia()` - Adicionar log de atualização
- [ ] `criar_pendencias_automaticas()` - Usar helper específico

### RelatorioService
- [ ] `aprovar_relatorio()` - Usar `audit_aprovar_relatorio`
- [ ] `rejeitar_relatorio()` - Usar `audit_rejeitar_relatorio`
- [ ] `enviar_relatorio()` - Adicionar log de envio

### ConfigService
- [ ] `update_pendencias_intervalo_dias()` - Log de config
- [ ] `update_lembretes_config()` - Log de config
- [ ] `update_alertas_vencimento_config()` - Log de config
- [ ] `update_escalonamento_config()` - Log de config
- [ ] `upload_modelo_relatorio()` - Log de upload
- [ ] `remove_modelo_relatorio()` - Log de remoção

## ⚠️ Notas Importantes

1. **Não falhe operações por erro de log**: Sempre use try/except ao criar logs
2. **Dados sensíveis**: Não logue senhas ou tokens nos dados JSON
3. **Performance**: Os logs são assíncronos e não devem impactar performance
4. **Opcional**: Se `current_user` não estiver disponível, o log simplesmente não é criado

## 🔍 Como Verificar

Após integrar, verifique se os logs estão sendo criados:

```sql
-- Ver últimos logs criados
SELECT * FROM audit_log ORDER BY data_hora DESC LIMIT 10;

-- Ver logs de um contrato específico
SELECT * FROM audit_log
WHERE entidade = 'CONTRATO' AND entidade_id = 123
ORDER BY data_hora DESC;

-- Ver logs de um usuário
SELECT * FROM audit_log
WHERE usuario_id = 1
ORDER BY data_hora DESC LIMIT 20;
```

Ou use a página de Logs de Auditoria no frontend: `/logs-auditoria`

## 📊 Endpoints Disponíveis

- `GET /api/v1/audit-logs` - Lista todos os logs (com filtros)
- `GET /api/v1/audit-logs/statistics` - Estatísticas
- `GET /api/v1/audit-logs/{id}` - Log específico
- `GET /api/v1/audit-logs/entidade/{entidade}/{id}` - Logs de uma entidade
- `GET /api/v1/audit-logs/usuario/{id}` - Logs de um usuário

---

**Última atualização**: 2025-09-30
**Versão do sistema**: 2.5
