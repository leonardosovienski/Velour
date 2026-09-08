# Cadastro, recuperação de conta e cobrança — implementação atual

O Velour possui cadastro de salão, teste de 14 dias, cobrança por um preço mensal configurado no Stripe e portal de assinatura hospedado pelo provedor. Este documento descreve o comportamento implementado; o nome `ONBOARDING_BILLING_PLAN.md` foi mantido para preservar os links existentes.

Consulte [MULTI_TENANCY_PLAN.md](MULTI_TENANCY_PLAN.md) para isolamento e [PRODUCTION.md](PRODUCTION.md) para instalação, configuração e validação operacional. A existência da integração no código não significa que chaves, preço, webhook, SMTP ou portal já estejam configurados em uma instalação.

## Endpoints e permissões

Os caminhos abaixo são os da API. No deployment com proxy incluído no projeto, o navegador utiliza o prefixo `/api`.

| Endpoint | Acesso | Finalidade |
| --- | --- | --- |
| `GET /tenants/signup-config` | Público | Informa disponibilidade de cadastro, duração do teste e links/versão dos termos |
| `POST /tenants/signup` | Público, se habilitado | Cria salão e primeiro administrador |
| `POST /auth/login` | Público | Autentica por e-mail e senha |
| `GET /auth/me` | Usuário autenticado | Retorna a identidade atual, incluindo `tenant_id` |
| `POST /auth/forgot-password` | Público | Solicita link de recuperação por e-mail |
| `POST /auth/reset-password` | Token de recuperação válido | Redefine a senha e revoga sessões anteriores |
| `GET /billing/status` | Usuário autenticado | Informa assinatura, datas, acesso permitido e disponibilidade de gestão |
| `POST /billing/checkout-session` | `admin` do salão | Abre ou reutiliza Checkout |
| `POST /billing/portal-session` | `admin` do salão | Abre o portal do cliente Stripe |
| `POST /billing/webhook` | Assinatura Stripe válida | Atualiza a assinatura com dados verificados no provedor |
| `GET /tenants/export` | `admin` do salão | Exporta os dados da conta em JSON |

Gerentes e profissionais podem consultar a situação da assinatura, mas não gerenciar cobrança nem exportar a conta completa.

## Cadastro e teste de 14 dias

[routers/tenants.py](routers/tenants.py) recebe, por exemplo:

```json
{
  "tenant_name": "Salão Exemplo",
  "admin_name": "Responsável Exemplo",
  "admin_email": "responsavel@example.com",
  "admin_password": "uma-senha-forte-exclusiva",
  "accepted_terms": true
}
```

O [schema de cadastro](schemas/tenant.py) exige nomes válidos, e-mail, senha de 12 a 128 caracteres e aceite explícito dos termos. Campos extras são recusados. O e-mail é normalizado e precisa ser único entre todos os salões.

O cadastro cria o `Tenant` e seu primeiro `User(role=admin)` na mesma transação. O salão começa com `subscription_status=trialing`, vencimento em 14 dias e registro da data e versão do aceite. O slug combina o nome normalizado com um sufixo aleatório. A resposta contém o JWT para entrada imediata.

O cadastro não chama o Stripe: o Customer é criado quando o administrador inicia o Checkout. Não há cobrança nem exigência de cartão na criação da conta. Também não há e-mail de boas-vindas ou confirmação de titularidade do e-mail implementados; a validação inicial verifica o formato do endereço.

`SIGNUP_ENABLED=false` desabilita novos cadastros sem remover o acesso das contas existentes. Em produção, esse é o padrão. Habilitar o cadastro exige URLs HTTPS de termos e privacidade e configuração básica de SMTP. A validação de configuração não substitui verificar se essas páginas e o envio de e-mail funcionam.

## Checkout mensal

[routers/billing.py](routers/billing.py) executa o Checkout sob trava de cobrança e bloqueio da linha do salão no PostgreSQL:

1. Cria o Customer, caso necessário, usando chave de idempotência derivada do salão.
2. Consulta as assinaturas do Customer e recusa criar outra quando existir uma assinatura em estado não terminal. Nessa situação, o usuário deve gerenciar a existente pelo portal.
3. Procura uma sessão de Checkout aberta da mesma conta e a reutiliza quando possível. Listagens incompletas que impediriam verificar duplicidade levam a recusa da operação.
4. Valida o preço configurado: ativo, recorrente, mensal, intervalo de um mês e ambiente de teste/produção correspondente.
5. Cria a sessão hospedada com uma unidade do preço, identificação do salão e URLs de retorno derivadas de `APP_URL`.
6. Guarda ID e expiração da sessão e devolve a URL do Stripe.

O frontend redireciona para o Checkout hospedado. O Velour não recebe os campos de cartão desse formulário. O retorno `?checkout=success` não libera acesso e não comprova pagamento: a confirmação ocorre pelo webhook.

Se o teste ainda estiver válido e não houver assinatura anterior vinculada, o Checkout recebe a data de fim do teste. Quando faltam menos de 49 horas, essa data é estendida para 49 horas após a criação do Checkout para atender à antecedência usada pela integração. Portanto, cadastrar cartão perto do fim do teste pode estender esse prazo.

O valor e a moeda vêm do preço Stripe selecionado por `STRIPE_PRICE_ID`. Não há preço comercial fixado no código. Alterar essa variável exige atualizar a configuração da API; não migra assinaturas existentes. Assinaturas de outro preço são consideradas `unsupported_plan` ao sincronizar. Uma troca de preço ou plano precisa ser planejada antes de alterar a variável em uma instalação com clientes.

## Portal e cancelamento

`POST /billing/portal-session` exige que a conta já tenha Customer. O portal é hospedado pelo Stripe e depende da configuração do Customer Portal nessa conta Stripe.

Os recursos disponíveis ao cliente, como atualização de pagamento ou cancelamento, dependem das opções habilitadas no portal. O Velour não implementa sua própria tela de cartão, cancelamento ou reembolso. Ele passa a aplicar a situação recebida na sincronização da assinatura; um cancelamento agendado para o fim do período segue o estado efetivo informado pelo Stripe.

## Webhooks e sincronização

O endpoint valida `Stripe-Signature` com `STRIPE_WEBHOOK_SECRET`, rejeita payloads acima de 512 KiB e confere o ambiente pelo campo `livemode`. Eventos relevantes incluem:

| Grupo | Eventos aceitos |
| --- | --- |
| Checkout | `checkout.session.completed`, `checkout.session.async_payment_succeeded` |
| Assinatura | `customer.subscription.created`, `updated`, `deleted`, `paused`, `resumed` |
| Fatura | `invoice.paid`, `invoice.payment_succeeded`, `invoice.payment_failed`, `invoice.payment_action_required` |

Na linha de assinatura, os nomes abreviados continuam com o prefixo `customer.subscription.`.

O evento não é aplicado como uma ordem direta para ativar ou cancelar acesso. O servidor localiza o Customer do salão, recupera a assinatura atual pela API Stripe e verifica Customer, metadado `tenant_id`, ambiente, preço e quantidade. Eventos atrasados de uma assinatura anterior não devem substituir uma assinatura nova ainda não terminal.

O ID do evento é registrado em `billing_webhook_events` na mesma transação da atualização. Reenvios de um evento já processado retornam indicação de duplicidade. Falhas de comunicação com o Stripe fazem rollback e retornam erro para permitir reentrega. Eventos fora da lista suportada são ignorados.

Os campos locais guardam o último estado sincronizado. Não existe job periódico de reconciliação com o Stripe. O operador precisa monitorar falhas e reentregar eventos pendentes; webhooks interrompidos podem deixar o estado local desatualizado ou bloquear acesso quando um período terminar.

## Regras de acesso

`require_active_subscription` está aplicado aos routers de usuários, clientes, profissionais, serviços, produtos, agendamentos, fidelidade, indicações, dashboard, relatórios e auditoria.

| Situação da conta | Condição de acesso aos recursos de negócio |
| --- | --- |
| `trialing` | `trial_ends_at` precisa existir e estar no futuro |
| `active` | `current_period_end` precisa existir e estar no futuro |
| `past_due` | Acesso por até 7 dias após `past_due_since` |
| Outros estados | Acesso recusado com HTTP 402 |
| Salão suspenso (`is_active=false`) | Autenticação recusada, independentemente da assinatura |

O início da carência usa a data da fatura atual não paga quando disponível; não usa simplesmente a chegada de um evento antigo. Uma nova sincronização de inadimplência não reinicia uma carência já iniciada. O código converte `canceled` para `cancelled` e `incomplete_expired` para `expired`; estados desconhecidos e planos não suportados não liberam acesso.

O vencimento do teste é calculado a cada verificação. Não existe um job que precise mudar o registro para `expired`: `/billing/status` apresenta esse estado quando o teste local venceu.

Mesmo sem assinatura válida, uma conta ainda ativa pode autenticar, consultar cobrança, abrir Checkout/portal e exportar seus dados. A leitura autenticada de fotos existentes também permanece disponível, respeitando salão e profissional. Suspensão administrativa é diferente de vencimento de cobrança e impede esses acessos autenticados.

## Recuperação e sessão no navegador

[routers/account_recovery.py](routers/account_recovery.py) implementa tokens de recuperação de uso único. O banco armazena somente o hash SHA-256 do segredo; o token original é enviado no link por e-mail. O prazo padrão é 30 minutos, configurável entre 5 e 60 minutos.

Uma nova solicitação invalida links anteriores ainda não usados. A resposta normal à solicitação não informa se o endereço possui conta; a recuperação só é emitida para usuário e salão ativos. SMTP ausente resulta em indisponibilidade explícita. O envio ocorre em tarefa de fundo do processo e não possui fila persistente nem garantia de reentrega.

A redefinição válida altera o hash da senha, consome os links pendentes e incrementa `token_version`, invalidando JWTs anteriores. O frontend guarda o JWT em `sessionStorage`, valida a identidade em `/auth/me` ao restaurar a sessão e elimina as credenciais legadas conhecidas de `localStorage`.

Não há MFA, confirmação de e-mail, refresh token ou lista de dispositivos. Sair no navegador remove a credencial local; não revoga por si só uma cópia do JWT que tenha sido obtida antes.

## Exportação e preservação de dados

A exportação inclui usuários, clientes, profissionais, categorias, serviços, produtos, receitas, agendamentos, movimentos de estoque, fidelidade, indicações e auditoria do salão. Ela exclui hashes de senha, `token_version`, tokens de recuperação e o registro global de webhooks.

O arquivo é JSON com cabeçalho para download e `Cache-Control: no-store`. Fotos aparecem como referências; os arquivos precisam ser baixados separadamente enquanto houver acesso autorizado. Não há ZIP com anexos, importação automática dessa exportação, exclusão automática após cancelamento ou execução automática de pedidos de eliminação de dados.

## Configuração e operação

| Variável | Uso |
| --- | --- |
| `APP_URL` | Origem pública da aplicação, usada em Checkout, portal e recuperação; `FRONTEND_URL` é fallback legado |
| `SIGNUP_ENABLED` | Abre ou fecha novos cadastros |
| `TERMS_URL`, `PRIVACY_URL`, `TERMS_VERSION` | Links exibidos e versão registrada no aceite |
| `STRIPE_SECRET_KEY` | Credencial de API do Stripe |
| `STRIPE_WEBHOOK_SECRET` | Segredo de assinatura do endpoint de webhook |
| `STRIPE_PRICE_ID` | Único preço mensal aceito pela integração |
| `STRIPE_LIVEMODE` | Ambiente esperado; padrão `false` para testes |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS` | Envio de e-mails conforme o provedor; TLS exigido em produção |
| `PASSWORD_RESET_EXPIRE_MINUTES` | Validade do link de recuperação |
| `TOKEN_EXPIRE_MINUTES` | Validade do JWT; padrão 480 minutos |

As variáveis disponíveis e exemplos estão em [.env.example](.env.example). Informar chaves não cria o preço, o endpoint de webhook ou as opções do portal no Stripe. Antes de abrir vendas, siga o procedimento de validação do [guia de produção](PRODUCTION.md), incluindo um ciclo de cobrança no ambiente de teste e entrega real de e-mail de recuperação.

Os limites implementados são: cadastro 5/hora por IP; exportação 3/hora por IP e usuário; abertura de sessões de cobrança 10/minuto por IP e usuário; solicitação de recuperação 5/15 minutos por IP e 3/hora por e-mail; consumo do link 10/15 minutos por IP. Os contadores ficam em memória e são reiniciados com a API. Eles reduzem abuso, mas não impedem tentativas distribuídas ou criação de múltiplas contas com endereços diferentes.

## Testes e capacidades ainda ausentes

[test_saas.py](tests/test_saas.py) cobre cadastro, recuperação, cobrança, assinatura de webhook, idempotência, estados de acesso e exportação usando integrações simuladas. Testes de isolamento e concorrência estão relacionados no [documento de arquitetura](MULTI_TENANCY_PLAN.md). Testes simulados não verificam as credenciais, o portal ou a entregabilidade de SMTP da instalação real.

O produto atualmente não implementa múltiplos planos, cobrança por usuário ou consumo, cupons administrados pelo Velour, migração de plano, emissão fiscal automática, reembolso pela aplicação, CAPTCHA, verificação de e-mail, filas persistentes ou reconciliação automática de cobrança. Esses itens precisam de implementação ou processo operacional próprio quando fizerem parte da oferta comercial.
