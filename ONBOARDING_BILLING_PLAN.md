# Plano técnico — Onboarding self-serve + Billing (Stripe)

> Documento de planejamento, não implementado ainda. Assume as decisões de
> produto já fechadas: assinatura mensal fixa (valor configurável, não
> definido aqui), trial de 14 dias, cadastro self-serve, gateway Stripe.
> Complementa o [`MULTI_TENANCY_PLAN.md`](./MULTI_TENANCY_PLAN.md) — **este
> plano depende do núcleo de multi-tenancy já estar implementado** (ver
> seção 0).

## 0. Pré-requisito: por que isso não pode vir antes de multi-tenancy

Cadastro self-serve significa "qualquer salão cria a própria conta sozinho" —
ou seja, cria um novo tenant. Sem o modelo `Tenant` e o isolamento de dados
por `tenant_id` (seções 2–3 do `MULTI_TENANCY_PLAN.md`), não existe "conta
nova" para criar: hoje o sistema assume um único salão. Sequenciamento
mínimo:

1. `MULTI_TENANCY_PLAN.md` seções 1–3 (modelo `Tenant`, `tenant_id` nas
   tabelas, escopo por tenant no auth) — **bloqueante**.
2. Este plano (onboarding + billing) — usa o `Tenant` já existente.
3. `MULTI_TENANCY_PLAN.md` seções 6–11 (uploads particionados, jobs,
   painel superadmin, testes de isolamento) podem vir em paralelo ou depois
   — não bloqueiam onboarding/billing.

## 1. Campos novos em `Tenant`

```python
class Tenant(Base):
    ...  # id, name, slug, cnpj/cpf, is_active (já no MULTI_TENANCY_PLAN.md)
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    subscription_status: Enum(trialing, active, past_due, cancelled, expired)
    trial_ends_at: datetime
    current_period_end: datetime | None
```

`subscription_status` só é alterado a partir de webhooks do Stripe (nunca
por uma requisição do cliente) — é a fonte da verdade sobre pagamento.

## 2. Fluxo de cadastro (signup)

```
POST /tenants/signup   (público, sem autenticação)
body: { tenant_name, admin_name, admin_email, admin_password }
```

1. Cria `Tenant(subscription_status=trialing, trial_ends_at=now()+14d)`.
2. Cria `Stripe Customer` vinculado ao tenant (guarda `stripe_customer_id`) —
   já nesse momento, mesmo sem cartão cadastrado, para simplificar o
   checkout depois.
3. Cria o primeiro `User(role=admin, tenant_id=tenant.id)`.
4. Envia e-mail de boas-vindas (reaproveita `email_service.py`).
5. Retorna um `access_token` já válido — login automático, o admin cai
   direto no sistema sem precisar logar de novo.

**Segurança do endpoint público:**
- Rate limit por IP via `rate_limit.py` (ex.: 5 cadastros/hora por IP) —
  hoje só login/clientes/agendamentos são limitados, esse endpoint fica
  exposto sem autenticação e é alvo natural de abuso (spam de trials).
- Validar e-mail (formato + confirmação por clique, se decidirem exigir
  antes de liberar o trial — recomendado para reduzir trials fantasmas,
  mas adiciona uma etapa; pode ficar para uma v2 se quiser lançar mais
  rápido).
- Senha com política mínima já existente no schema de usuário.

## 3. Checkout — adicionar forma de pagamento

Antes do trial acabar (ou a qualquer momento), o admin do salão inicia o
checkout:

```
POST /billing/checkout-session   (autenticado, admin do tenant)
→ cria uma Stripe Checkout Session vinculada ao stripe_customer_id do tenant
→ retorna a URL de checkout hospedada pelo Stripe
```

Usar **Stripe Checkout hospedado** (não Payment Intents customizados) — o
frontend só redireciona para a URL que o Stripe devolve. Isso evita lidar
com dados de cartão diretamente (menor escopo de PCI-DSS) e é o caminho
mais rápido de implementar.

O preço em si (`STRIPE_PRICE_ID`) é configurado no Stripe Dashboard e lido
de uma variável de ambiente — muda o valor da assinatura sem precisar
alterar/redeployar código.

## 4. Webhook do Stripe

```
POST /billing/webhook   (público, verificado por assinatura Stripe)
```

Eventos a tratar:

| Evento Stripe | Efeito |
|---|---|
| `checkout.session.completed` | `subscription_status = active`, guarda `stripe_subscription_id` |
| `invoice.payment_failed` | `subscription_status = past_due` |
| `invoice.payment_succeeded` (após past_due) | `subscription_status = active` |
| `customer.subscription.deleted` | `subscription_status = cancelled` |

A assinatura do webhook (`Stripe-Signature` header + `STRIPE_WEBHOOK_SECRET`)
**precisa** ser verificada — sem isso, qualquer um poderia forjar um evento
e liberar acesso sem pagar.

Um job separado (reaproveitando o padrão do `reminder_scheduler.py`) varre
diariamente tenants com `subscription_status=trialing` e `trial_ends_at`
vencido, movendo para `expired` — cobre o caso do usuário nunca voltar para
finalizar o checkout.

## 5. Bloqueio de acesso por status de assinatura

Uma dependency nova (`require_active_subscription`, no mesmo espírito de
`require_admin`), aplicada a todos os routers de negócio (não à própria rota
de billing/checkout, óbvio):

- `trialing` e `active` → acesso normal.
- `past_due` → acesso normal por um período de carência curto (ex.: 7 dias),
  com aviso no frontend — evita cortar o salão no meio do expediente por uma
  falha pontual de cobrança.
- `expired`/`cancelled` (fora da carência) → bloqueia com HTTP 402, frontend
  redireciona para a tela de billing.

Dado que os dados do tenant continuam no banco mesmo bloqueado, considerar
uma rota de exportação que continua liberada mesmo sem assinatura ativa
(alinhado com a promessa de exportação no `TERMOS_DE_USO.md` seção 6).

## 6. Frontend

- `/signup` — página pública nova, formulário de cadastro.
- `/billing` — status da assinatura (dias restantes de trial, ou "ativo
  desde X"), botão para iniciar checkout ou trocar forma de pagamento
  (Stripe Customer Portal, que também é hospedado — evita construir tela de
  gestão de cartão).
- Banner/bloqueio global quando `subscription_status` não é `trialing`/`active`.
- `AuthContext` passa a expor `subscription_status` (vem no payload de
  `/auth/me` ou do JWT) para o frontend decidir quando mostrar o banner.

## 7. Variáveis de ambiente novas

```
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRICE_ID
```

## 8. Fora de escopo deste plano (decidir depois)

- Upgrade/downgrade de plano (só existe um plano fixo por enquanto).
- Cobrança proporcional (proration) — o modelo mensal fixo simples não
  precisa disso inicialmente.
- Nota fiscal automática — depende de qual serviço de emissão for escolhido;
  pode ficar manual no começo.
- CAPTCHA/anti-bot no signup — mencionado como possível v2 na seção 2.

## 9. Ordem de implementação sugerida

1. Núcleo de multi-tenancy (pré-requisito, seção 0).
2. Campos de billing em `Tenant` + `POST /tenants/signup` sem Stripe ainda
   (só cria o trial) — já dá para testar onboarding de ponta a ponta.
3. Integração Stripe: customer no signup, checkout session, webhook.
4. `require_active_subscription` + bloqueio no frontend.
5. Customer Portal / cancelamento self-serve.
