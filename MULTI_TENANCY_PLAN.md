# Plano de Multi-tenancy — Velour SaaS

> Documento de planejamento, não implementado ainda. Mapeia o que precisa
> mudar para o Velour deixar de ser "um deploy = um salão" e passar a
> suportar vários salões (tenants) na mesma instância/banco, isolados entre
> si. Serve de base para dimensionar o esforço antes de decidir quando
> começar.

## 1. Decisão de arquitetura: schema compartilhado com `tenant_id`

Três estratégias possíveis para isolar dados de vários salões:

| Estratégia | Isolamento | Custo operacional | Recomendação |
|---|---|---|---|
| **Schema compartilhado + `tenant_id`** | Lógico (por linha) | Baixo — 1 banco, 1 deploy | ✅ Recomendado para MVP |
| Schema por tenant (mesmo banco) | Médio | Médio — migração roda N vezes | Considerar se exigirem isolamento forte |
| Banco por tenant | Forte | Alto — N bancos para provisionar/migrar/backupar | Só se exigido por contrato/compliance |

Recomendo começar por schema compartilhado: é o caminho mais rápido para
validar o modelo SaaS, e dá para migrar para isolamento mais forte depois
para clientes específicos que exijam isso.

## 2. Modelo de dados

### 2.1 Nova entidade `Tenant` (Salão)

```python
class Tenant(Base):
    id, name, slug (subdomínio, único), cnpj/cpf, is_active,
    subscription_status (trialing/active/past_due/cancelled), created_at
```

### 2.2 Adicionar `tenant_id` em toda tabela com dado de negócio

`users`, `clients`, `professionals`, `services`, `service_categories`,
`products`, `service_recipes`, `appointments`, `loyalty_transactions`,
`referrals`, `stock_movements`, `audit_logs`.

Para cada uma: `tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)`.

### 2.3 Constraints únicas hoje globais que precisam virar compostas

- `clients.code` (`VLR-00001`) → único por `(tenant_id, code)`; contador
  sequencial também precisa ser por tenant (`routers/clients.py: _next_vlr_code`).
- `clients.referral_code` → pode continuar globalmente único (gerado
  aleatório) ou virar `(tenant_id, referral_code)` — decidir se indicação
  cross-tenant deve ser impedida (provavelmente sim, então manter único
  globalmente é mais simples e já resolve isso).
- `users.email` → hoje único globalmente (`ix_users_email`). Decisão de
  produto: um mesmo e-mail pode ter conta em salões diferentes? Se sim, vira
  único por `(tenant_id, email)` e o login precisa perguntar/detectar o
  tenant antes ou junto da autenticação.

### 2.4 Migração dos dados existentes

Uma migration Alembic que:
1. Cria a tabela `tenants`.
2. Insere um tenant "legado" (o salão atual).
3. Adiciona `tenant_id` nullable em todas as tabelas, popula com o id do
   tenant legado, depois altera para `NOT NULL`.

## 3. Autenticação e escopo por tenant

- JWT passa a carregar `tenant_id` no payload (`auth.py: create_access_token`).
- `get_current_user`/`require_admin`/`ensure_professional_scope` precisam
  validar que o recurso acessado pertence ao `tenant_id` do token — hoje eles
  só checam role/professional_id.
- **Ponto crítico de segurança:** toda query em todo router precisa filtrar
  por `tenant_id`. Esquecer um filtro em um único endpoint vaza dados entre
  salões. Formas de mitigar sistematicamente:
  - Um `get_db` que já devolve uma `Session` com filtro automático de tenant
    (SQLAlchemy `with_loader_criteria` global, aplicado uma vez).
  - Ou uma camada de repositório única por modelo que sempre exige
    `tenant_id` como primeiro argumento (mais invasivo, mas explícito).
  - De qualquer forma: **testes de isolamento** são obrigatórios — criar 2
    tenants nos testes e afirmar que endpoints de um nunca retornam dados do
    outro (esse teste hoje não existe e não faz sentido existir num sistema
    single-tenant).

## 4. Identificação do tenant na requisição

Opções, da mais comum em SaaS para a menos:

1. **Subdomínio** (`salao-a.velour.app`, `salao-b.velour.app`) — o backend
   resolve o tenant pelo `Host` header. Mais transparente para o usuário
   final, mas exige wildcard DNS/certificado e ajuste no CORS
   (`CORS_ORIGINS` deixa de ser lista fixa).
2. **Login por e-mail único** (sem subdomínio) — o backend descobre o tenant
   pelo e-mail no login e emite o JWT já escopado; todas as chamadas
   seguintes usam esse token. Mais simples de implementar agora, mas exige
   e-mail único mesmo entre tenants (ver 2.3).
3. Header/param explícito (`X-Tenant-Id`) — mais simples tecnicamente, mas
   pior experiência (o cliente escolhe/digita o tenant) e mais fácil de
   errar/forjar se não validado contra o JWT.

Recomendo (2) para começar — não exige mudança de infra de DNS/certificado —
migrando para (1) quando o número de salões justificar.

## 5. Onboarding de novo salão

Hoje o primeiro admin é criado via `bootstrap_admin.py` (manual, uma vez).
Precisa virar um fluxo repetível:

- Endpoint público `POST /tenants/signup` (ou painel administrativo da
  Velour) que cria o `Tenant` + primeiro usuário admin.
- Definir se há período de trial antes de exigir pagamento.
- E-mail de boas-vindas/confirmação (reaproveita `email_service.py`).

## 6. Uploads de fotos

`uploads/{filename}` hoje é uma pasta única. Precisa:
- Particionar por tenant: `uploads/{tenant_id}/{filename}`.
- `GET /uploads/{filename}` (`main.py`) precisa verificar que o arquivo
  pertence ao tenant do usuário autenticado, não só que o usuário está
  autenticado (hoje qualquer usuário logado, de qualquer tenant, acessaria
  qualquer arquivo pelo nome — furo de isolamento se não corrigido).

## 7. Jobs agendados

`birthday_scheduler.py` e `reminder_scheduler.py` hoje rodam uma query
global. Precisam iterar por tenant (ou continuar globais, já que a query já
filtraria por tenant_id nas tabelas — o job em si não muda muito, só as
queries internas). Ponto de atenção: fuso horário do "aniversário às 08h" —
hoje é um horário fixo do servidor; com salões em fusos diferentes, considerar
se isso importa (provavelmente não, para o escopo do Brasil).

## 8. Rate limiting

`rate_limit.py` já usa `(ip, user_id)` como chave — como cada usuário
pertence a um tenant, isso já isola por tenant automaticamente. Nenhuma
mudança necessária aqui.

## 9. Cobrança (billing)

Fora do escopo deste plano técnico, mas é pré-requisito de produto:
- Gateway de pagamento (Stripe é o mais direto para SaaS B2B).
- Campo `subscription_status` no `Tenant`, atualizado via webhook do gateway.
- Middleware/dependency que bloqueia acesso (ou degrada para read-only) se
  `subscription_status` não for `active`/`trialing`.

## 10. Painel da Velour (superadmin)

Hoje não existe conceito de "equipe da Velour" olhando todos os tenants —
só existe `admin`/`manager`/`professional` dentro de um salão. Precisa de um
novo papel (`platform_admin` ou tabela separada de usuários da plataforma)
para: listar tenants, ver status de assinatura, suspender conta, suporte.

## 11. Testes e seed

- `seed.py` e `tests/conftest.py` assumem dados sem tenant — helpers como
  `make_client`/`make_appointment` precisam de um `tenant_id` (provavelmente
  um fixture `tenant` que cria um `Tenant` de teste).
- Testes de isolamento (mencionados na seção 3) são a rede de segurança mais
  importante deste projeto — sem eles, uma regressão de isolamento entre
  salões pode passar despercebida no CI.

## 12. Estimativa de esforço (ordem de grandeza)

| Frente | Esforço relativo |
|---|---|
| Modelo de dados + migration | Médio |
| Auth/escopo por tenant + testes de isolamento | Alto — é o núcleo, precisa ser bem feito |
| Onboarding de novo salão | Médio |
| Uploads particionados | Baixo |
| Billing | Médio–Alto (depende do gateway escolhido) |
| Painel superadmin | Médio |
| Frontend (nenhuma mudança estrutural grande — token já escopa tudo via API) | Baixo |

No geral, é um projeto de várias semanas, não um ajuste pontual — vale
tratar como uma fase separada do roadmap, com plano próprio de implementação
quando for priorizado.
