# Velour — manual funcional e referência técnica

Este documento descreve o comportamento implementado no repositório. O Velour é um SaaS de gestão para equipes de salões: cada salão tem seus usuários, clientes, agenda, estoque e assinatura. Clientes atendidos pelo salão são registros do sistema; não possuem portal de autoagendamento ou login próprio.

Para instalar e desenvolver, consulte o [README](README.md). Para publicar, configurar Stripe/SMTP, operar backups e homologar pagamentos, siga o [guia de produção](PRODUCTION.md). Código implementado e testes automatizados não substituem a homologação do ambiente que receberá clientes reais.

## 1. Arquitetura e configuração

```text
Navegador → React + TypeScript → /api → FastAPI + SQLAlchemy → PostgreSQL
                                             ├─ Stripe Checkout e Portal
                                             ├─ SMTP transacional
                                             └─ volume privado de fotos
```

- O frontend usa `VITE_API_URL`, com `/api` como padrão. O Vite encaminha `/api` para `http://127.0.0.1:8000` no desenvolvimento; o Nginx faz esse encaminhamento nos containers.
- SQLite serve para desenvolvimento/testes. `APP_ENV=production` exige PostgreSQL e `AUTO_CREATE_TABLES=false`; o schema é atualizado pelo Alembic.
- A implantação suportada tem **uma réplica da API e um worker**. Locks, limites de requisições e agendadores são locais ao processo. Em produção, uma conexão PostgreSQL mantém um advisory lock que impede uma segunda API no mesmo banco.
- `SECRET_KEY` é obrigatória. A configuração de produção valida o segredo, origens HTTPS explícitas, banco e demais condições em [config.py](config.py).
- `/docs`, `/redoc` e `/openapi.json` estão disponíveis fora de produção e desabilitados em produção. `/health` verifica uma consulta ao banco; não testa entrega SMTP ou recebimento de pagamentos.

Não é necessário executar `seed.py` para criar uma conta. Ele é opcional, permitido apenas em desenvolvimento, e apaga/recria os dados do salão `demo`. Não serve para migrar um banco nem para inicializar produção.

## 2. Conta, acesso e assinatura

### Cadastro e primeiro acesso

1. Quando `SIGNUP_ENABLED=true`, `/signup` permite informar nome do salão, nome do administrador, e-mail e senha de 12 a 128 caracteres, com aceite dos termos. O `.env.example` mantém o cadastro desabilitado até a configuração deliberada do operador.
2. A API cria um salão independente e seu primeiro usuário `admin`, registra a data/versão do aceite e inicia **14 dias de teste**, sem depender da disponibilidade do Stripe.
3. A sessão é iniciada e o usuário chega a `/billing?welcome=1`. Um salão novo começa sem clientes, profissionais, categorias, serviços ou produtos.
4. Cadastre categorias e serviços, profissionais e usuários; depois clientes e agendamentos. Estoque e fichas técnicas são necessários quando houver controle de insumos.

O e-mail de login é normalizado para minúsculas e único na plataforma. Um login pertence a um salão; não há seletor de múltiplos salões na sessão. Para instalar com cadastro fechado, [bootstrap_admin.py](bootstrap_admin.py) cria um administrador por solicitação interativa, após aplicar as migrações.

### Sessão e recuperação de senha

`POST /auth/login` recebe formulário OAuth2 com `username` (o e-mail) e `password`. A resposta inclui token Bearer, nome, papel, vínculo profissional e salão. O frontend guarda o token em `sessionStorage` e consulta `/auth/me` ao restaurar a sessão. O padrão de expiração é 480 minutos, configurável por `TOKEN_EXPIRE_MINUTES`.

O backend consulta usuário e salão ativos em cada autenticação. Não concede permissão com base apenas no papel informado pelo navegador ou pelo JWT. Mudanças de papel, vínculo profissional ou ativação incrementam `token_version`; redefinir senha também revoga sessões anteriores. O botão Sair remove a sessão daquele navegador, sem revogar por si só todos os tokens já emitidos.

`/forgot-password` solicita um link por e-mail. Com SMTP disponível, a resposta não revela se a conta existe. O link é de uso único e expira em 30 minutos por padrão (`PASSWORD_RESET_EXPIRE_MINUTES`, entre 5 e 60). A solicitação de um novo link invalida os anteriores. Sem SMTP configurado, a API informa indisponibilidade (503).

### Papéis e permissões

Todas as permissões se limitam ao salão autenticado. `require_admin` e `require_manager` aceitam `admin` e `manager`; `require_owner` aceita apenas `admin`.

| Ação | `admin` | `manager` | `professional` |
|---|---|---|---|
| Assinar, abrir Portal Stripe e exportar dados do salão | Sim | Não | Não |
| Consultar situação da assinatura | Sim | Sim | Sim |
| Criar/alterar administradores | Sim | Não | Não |
| Gerenciar gerentes e usuários profissionais | Sim | Sim | Não |
| Cadastrar/editar/desativar clientes | Sim | Sim | Não |
| Consultar clientes e briefing | Salão | Salão | Clientes vinculados por agendamento |
| Operar agenda, concluir atendimento e acessar fotos | Salão | Salão | Próprio `professional_id` |
| Cadastrar/editar profissionais, serviços e categorias | Sim | Sim | Não |
| Ler serviços e fichas técnicas | Sim | Sim | Sim |
| Gerenciar estoque e fichas técnicas | Sim | Sim | Não |
| Visão geral de fidelidade, indicações, relatórios e auditoria | Sim | Sim | Não |

Usuários `professional` precisam de vínculo com um profissional ativo do mesmo salão; um profissional não pode ser vinculado a dois usuários. O último administrador ativo não pode ser desativado nem perder esse papel. Não existe papel de administrador da plataforma na API pública: suporte entre salões é feito por ferramenta local, descrita em [PRODUCTION.md](PRODUCTION.md).

Consulte os escopos dos endpoints abaixo ao criar integrações. A existência de um item no menu não substitui autorização da API.

### Cobrança e bloqueio

Em **Conta e assinatura** (`/billing`), qualquer usuário vê a situação da conta. Apenas administradores podem abrir o Checkout, gerenciar a assinatura no Portal Stripe ou exportar dados.

| Situação | Acesso às rotas de negócio |
|---|---|
| `trialing` | Até `trial_ends_at` |
| `active` | Até `current_period_end` |
| `past_due` | Até 7 dias após `past_due_since` |
| Demais situações ou prazo vencido | Bloqueado com HTTP 402 |
| Salão desativado pelo operador | Autenticação recusada |

O frontend encaminha respostas 402 para `/billing`. A conta com assinatura vencida ainda pode autenticar, consultar cobrança e, se o usuário for administrador, regularizar ou exportar dados. O acesso autenticado às fotos também não exige assinatura ativa, mas mantém a verificação do salão e do profissional.

O plano configurado é um único Price mensal recorrente do Stripe. Checkout e Portal retornam uma URL hospedada; o sistema não coleta cartões. O retorno `?checkout=success` não libera acesso por si só: webhooks com assinatura válida consultam a assinatura atual no Stripe, validam cliente, salão, plano e ambiente, e persistem o evento para evitar reprocessamento.

Ao aderir durante o teste, o Checkout preserva o prazo restante. Perto do vencimento, pode estendê-lo até pelo menos 49 horas a partir da abertura do Checkout, por exigência desse fluxo. Cancelamento e forma de pagamento são gerenciados no Portal; suas opções devem ser configuradas no Stripe pelo operador. O período efetivamente permitido é o exibido pela API, após sincronização.

## 3. Telas e operação diária

| Tela | Uso |
|---|---|
| Dashboard `/` | Agenda de hoje, receita, indicadores, próximos atendimentos, aniversariantes, clientes Platinum e alertas de estoque. Os dados de agendamento são filtrados para o profissional autenticado; alertas de estoque não são exibidos para esse papel. |
| Clientes `/clients` | Cadastro, filtro por tier/gênero/inatividade e acesso ao perfil. O perfil `/clients/:id` reúne preferências, alergias, fidelidade, histórico e indicações conforme as permissões. |
| Agendamentos `/appointments` | Criar agenda, filtrar período/status, abrir briefing, alterar status, cancelar, registrar conclusão e fotos. |
| Profissionais `/professionals` | Cadastro, comissão e meta mensal; estatísticas e painel de clientes a recuperar segundo sua cadência de retorno. Usuários profissionais só recebem o próprio perfil na lista e nas estatísticas. |
| Serviços `/services` | Catálogo, categorias e ficha técnica de insumos por serviço. |
| Estoque `/inventory` | Cadastro de insumos, entradas, perdas, ajustes, validade e histórico de movimentações. Acesso administrativo. |
| Fidelidade `/loyalty` | Visão geral de pontos, distribuição de tiers e transações. A visão geral exige administrador ou gerente. |
| Indicações `/referrals` | Lista de indicações pendentes/convertidas e ranking. Acesso administrativo. |
| Relatórios `/reports` | Receita, clientes, fidelidade e indicações por período. Acesso administrativo. |
| Usuários `/users` | Cadastro, papel, vínculo profissional e ativação de usuários. |
| Conta e assinatura `/billing` | Situação do teste/assinatura, Checkout, Portal e exportação conforme o papel. |

O briefing é um painel de preparação do atendimento com preferências, alergias, observações e último atendimento concluído. Esses registros exigem acesso autorizado e merecem o mesmo cuidado dado às fotos e aos dados cadastrais.

## 4. Regras de negócio

### Agendamento e conclusão

- A criação exige cliente, profissional e serviço ativos do mesmo salão. `ends_at` é calculado pelo servidor: início mais a duração do serviço.
- Há conflito se `existente.scheduled_at < novo.ends_at` e `existente.ends_at > novo.scheduled_at` para o mesmo profissional. A API retorna 409; `cancelled` e `no_show` não ocupam horário. Atendimentos adjacentes são permitidos.
- Estados: `scheduled`, `confirmed`, `in_progress`, `completed`, `cancelled`, `no_show`. `completed` só é aceito pelo endpoint próprio de conclusão.
- Um atendimento concluído, cancelado ou marcado como ausência não pode ser reaberto por alteração de status. Para reagendar, crie outro registro.
- A conclusão grava cobrança, fidelidade, indicação e consumo de estoque na mesma transação. Uma segunda conclusão retorna 409 e não concede os pontos novamente.
- `price_charged` no pedido de conclusão é o valor base antes dos descontos. Na resposta, é o valor final calculado pelo servidor. Não use apenas o cálculo de prévia da interface para gravar valores financeiros.
- `paid`, `amount_paid` e `payment_method` registram o pagamento do atendimento, separadamente da assinatura SaaS. Se `paid=true`, valor recebido e método são obrigatórios. Métodos: `cash`, `debit_card`, `credit_card`, `pix`, `other`. Esse registro não processa pagamentos nem emite documento fiscal.

### Fidelidade, descontos e indicações

| Tier | Gasto acumulado | Desconto no atendimento |
|---|---|---|
| Bronze | Menos de R$ 500 | 0% |
| Silver | R$ 500 a menos de R$ 1.500 | 5% |
| Gold | R$ 1.500 a menos de R$ 3.000 | 10% |
| Platinum | R$ 3.000 ou mais | 15% |

O desconto usa o tier anterior à conclusão. O servidor aplica primeiro o desconto do tier e depois o resgate, respeitando o teto combinado de 50% do valor base. O agendamento preserva `tier_at_service` e `tier_discount_amount`.

O resgate deve ser múltiplo de 100 pontos e não pode superar o saldo: 100 pontos correspondem a R$ 10. **Todos os pontos solicitados são debitados mesmo se o teto reduzir o desconto efetivo.** A equipe deve conferir a prévia antes de concluir.

O ganho é `service.points_reward` quando positivo; caso contrário, a parte inteira do valor final em reais, a 1 ponto por real. O gasto acumulado recebe o valor final, as visitas são incrementadas e o tier é recalculado. Não há job de rebaixamento por inatividade nem expiração automática de pontos implementada.

Uma indicação pendente é convertida no primeiro atendimento concluído do indicado: 150 pontos para quem indicou e 75 para o indicado. Os códigos de cliente e indicação pertencem ao salão; não representam uma sequência global sem lacunas.

Com agendadores habilitados, o job de aniversário executa às 08h do fuso operacional e concede 100 pontos a clientes ativos de salões ativos, consultando transações para não repetir o bônus no mesmo mês. Os jobs não recuperam automaticamente todas as execuções perdidas durante indisponibilidade.

### Estoque, fotos e comunicação

O saldo inicial do produto gera movimentação. Depois, o saldo muda por `/products/{id}/stock` ou consumo de atendimento, não pelo PATCH cadastral. `qty` é positiva nas movimentações manuais: compra/ajuste somam e perda subtrai; perda acima do saldo é rejeitada. O consumo da ficha técnica pode deixar saldo negativo e gera alerta de reposição, sem impedir a conclusão.

A ficha técnica é substituída integralmente por `PUT /services/{id}/recipe`. Na conclusão, `recipe_overrides` troca a dosagem de um insumo ou inclui outro; `actual_qty=0` ignora o consumo daquele item. Cada baixa registra saldo anterior, posterior e vínculo com o atendimento. Não há rotas de edição/exclusão do histórico de estoque.

Fotos são enviadas em multipart pelo endpoint do atendimento, até **5 MiB por arquivo**, em JPEG, PNG ou WebP. A validação confere a assinatura inicial do conteúdo; não é um serviço de antivírus ou reprocessamento de imagens. O endpoint de conclusão não aceita vincular URLs arbitrárias: novas fotos devem passar pelo upload autenticado. O download exige autenticação e uma referência de foto pertencente a um atendimento acessível ao usuário.

SMTP configurado permite confirmação após criar o agendamento e lembrete para horários entre 24 e 25 horas à frente, no job executado a cada hora. `reminder_sent` evita envios normais repetidos após gravação bem-sucedida; não há fila durável ou garantia de entrega exatamente uma vez. A mensagem de confirmação é enviada de forma síncrona; o e-mail de recuperação usa tarefa em segundo plano do FastAPI.

### Datas, dinheiro e desativação

- Nascimento e validade usam `YYYY-MM-DD`. Na agenda, `scheduled_at` e filtros `date_from`/`date_to` usam ISO 8601 **sem fuso**, como `2030-02-05T23:30:00`; `Z` ou offsets como `-03:00` são rejeitados com 422. Envie o horário local do salão. No Compose, `SALON_TIMEZONE` configura o `TZ` de todos os salões da implantação, por padrão `America/Sao_Paulo`. Ainda não há fuso individual por salão. Confira agendamentos históricos gravados por versões que convertiam o formulário para UTC: a correção não reinterpreta registros antigos, cujo offset não foi armazenado.
- Prazos de assinatura, cadastro do salão e recuperação são calculados em UTC, mas vários campos são serializados sem sufixo de fuso. A tela de assinatura interpreta esses prazos como UTC. Não trate todos os campos de data como tendo a mesma convenção.
- Dinheiro usa `Decimal`/`Numeric` no backend. Os campos monetários dos schemas de resposta usam `JsonDecimal` para produzir números JSON (ou `null` quando permitido), preservando `Decimal` internamente. Comissão é uma fração de 0 a 1 na API (por exemplo, `0.40`), apresentada como percentual na interface.
- DELETE de cliente, profissional, serviço e produto desativa o registro (`is_active=false`). DELETE de agendamento cancela. Categoria é uma exclusão física: retorna 409 enquanto houver qualquer serviço vinculado, inclusive inativo. Transfira esses serviços para outra categoria antes de excluir.
- Desativação preserva histórico e não equivale a apagamento de dados pessoais. Cancelamento de assinatura também não apaga o banco. Exportação produz JSON sem senhas/tokens e com referências às fotos; os arquivos devem ser baixados separadamente. Não existe endpoint público de exclusão definitiva de um salão.

## 5. Referência da API

Os caminhos abaixo são os da API FastAPI. Pelo frontend/Compose, acrescente `/api`: `/auth/me` corresponde a `/api/auth/me`. Rotas privadas usam `Authorization: Bearer <token>`. Respostas de lista são arrays, sem envelope com total.

As rotas de negócio exigem assinatura válida, além do papel indicado. `A/G` significa administrador ou gerente; `Autenticado` inclui profissionais, com os escopos descritos. Os schemas completos estão em [schemas](schemas) e os contratos interativos em `/docs` no desenvolvimento.

### Conta e cobrança

| Método e caminho | Acesso e contrato |
|---|---|
| `GET /health` | Público; `{status, system, environment}`, ou 503 se o banco estiver indisponível. |
| `GET /tenants/signup-config` | Público; `{signup_enabled, trial_days, terms_url, privacy_url, terms_version}`. |
| `POST /tenants/signup` | Público quando habilitado; `{tenant_name, admin_name, admin_email, admin_password, accepted_terms: true}` → sessão, 201. Campos extras são rejeitados. |
| `POST /auth/login` | Formulário `username`, `password` → `{access_token, token_type, role, name, professional_id, tenant_id}`. |
| `GET /auth/me` | Autenticado; identidade atual sem senha. |
| `POST /auth/forgot-password` | Público; `{email}` → `{message}`. |
| `POST /auth/reset-password` | Público; `{token, new_password}` → `{message}`. |
| `GET /billing/status` | Autenticado; situação, prazos, `access_allowed`, `configured`, `can_manage_billing`, `has_billing_customer`. |
| `POST /billing/checkout-session` | Admin; sem dados de plano vindos do navegador → `{url}`. |
| `POST /billing/portal-session` | Admin com cliente Stripe → `{url}`. |
| `POST /billing/webhook` | Corpo original do evento e header `Stripe-Signature`; sem JWT, com verificação Stripe. Limite de 512 KiB. |
| `GET /tenants/export` | Admin, inclusive com assinatura vencida; download JSON com `format_version`, salão e tabelas. |
| `GET /uploads/{filename}` | Autenticado e autorizado para o atendimento; arquivo privado. |

### Usuários, clientes e profissionais

| Método e caminho | Acesso, filtros e observações |
|---|---|
| `GET /users` | A/G; usuários do salão. |
| `POST /users` | A/G; `{name, email, password, role, professional_id?}`. Criar admin exige admin. |
| `PATCH /users/{id}` | A/G; `{name?, role?, is_active?, professional_id?}`; proteção do último admin e revogação de sessão. |
| `GET /clients` | Autenticado; `tier`, `gender`, `inactive_days`, `is_active=true`, `limit=50`, `offset=0`; profissional vê clientes vinculados. |
| `GET /clients/{id}` | Autenticado; profissional precisa de vínculo por agendamento. |
| `GET /clients/{id}/briefing` | Mesmo acesso do cliente; inclui preferências, fidelidade e último atendimento. |
| `POST /clients` | A/G; cadastro conforme `ClientCreate`, incluindo código de indicação opcional. |
| `PATCH /clients/{id}` | A/G; campos de `ClientUpdate`. |
| `DELETE /clients/{id}` | A/G; desativa, 204. |
| `GET /professionals` | Autenticado; `is_active=true`; profissional vê somente o próprio vínculo. |
| `GET /professionals/{id}` | Autenticado; profissional restrito ao próprio vínculo. |
| `GET /professionals/{id}/stats` | Mesmo escopo; estatísticas do mês. |
| `GET /professionals/{id}/dashboard` | Mesmo escopo; meta/comissão e cadência de clientes. |
| `POST /professionals` | A/G; campos de `ProfessionalCreate`. |
| `PATCH /professionals/{id}` | A/G; campos de `ProfessionalUpdate`. |
| `DELETE /professionals/{id}` | A/G; desativa, 204. |

### Serviços e estoque

| Método e caminho | Acesso, filtros e observações |
|---|---|
| `GET /service-categories` | Autenticado. |
| `POST /service-categories` | A/G; `{name, gender_target?, icon?}`. |
| `PATCH /service-categories/{id}` | A/G; schema de categoria, com `name` obrigatório. |
| `DELETE /service-categories/{id}` | A/G; exclusão física; 409 se houver serviços vinculados, inclusive inativos. |
| `GET /services` | Autenticado; `category_id`, `is_active=true`. |
| `GET /services/{id}` | Autenticado. |
| `POST /services` | A/G; `{category_id, name, description?, duration_minutes, price, points_reward?}`. |
| `PATCH /services/{id}` | A/G; campos de `ServiceUpdate`; `category_id` precisa existir no mesmo salão. |
| `DELETE /services/{id}` | A/G; desativa, 204. |
| `GET /products` | A/G; `is_active=true`, `low_stock=false`. |
| `GET /products/{id}` | A/G. |
| `POST /products` | A/G; cadastro e saldo inicial de `ProductCreate`. |
| `PATCH /products/{id}` | A/G; `ProductUpdate` não inclui saldo. |
| `DELETE /products/{id}` | A/G; desativa, 204. |
| `POST /products/{id}/stock` | A/G; `{qty, type, description?}` → produto atualizado. |
| `GET /products/{id}/movements` | A/G; histórico em ordem decrescente. |
| `GET /services/{id}/recipe` | Autenticado; insumos e quantidades, sem saldo/custo do estoque. |
| `PUT /services/{id}/recipe` | A/G; array `[{product_id, qty_consumed}]`; substitui a receita, `[]` a remove. |

### Agenda, fidelidade e relatórios

| Método e caminho | Acesso, filtros e observações |
|---|---|
| `GET /appointments` | Autenticado; `date_from`, `date_to`, `status`, `professional_id`, `client_id`, `limit=50`, `offset=0`; profissional restrito à própria agenda. |
| `GET /appointments/{id}` | Mesmo escopo; resposta expandida com cliente/profissional/serviço. |
| `POST /appointments` | Mesmo escopo; `{client_id, professional_id, service_id, scheduled_at, occasion?, notes?}` → 201; conflito retorna 409. |
| `PATCH /appointments/{id}/status` | Mesmo escopo; `{status}`; conclusão exige endpoint abaixo. |
| `POST /appointments/{id}/complete` | Mesmo escopo; `AppointmentComplete`: valor base, pontos, notas, fórmula, consumo e dados de pagamento. |
| `POST /appointments/{id}/photos` | Mesmo escopo; multipart `photo_before?`, `photo_after?`. |
| `DELETE /appointments/{id}` | Mesmo escopo; cancela, 204. |
| `GET /loyalty/transactions` | Autenticado; `client_id`, `type`, `date_from`, `date_to`, `limit=50`, `offset=0`; profissional vê transações de clientes vinculados por agendamento, inclusive bônus sem atendimento associado. |
| `GET /loyalty/overview` | A/G; circulação de pontos, mês, tiers e ranking. |
| `GET /referrals` | A/G; `status`, `referrer_id`, `limit=50`, `offset=0`. |
| `GET /referrals/ranking` | A/G; ranking de indicações. |
| `GET /dashboard/today` | Autenticado; agenda, receita e contagem por status. |
| `GET /dashboard/kpis` | Autenticado; `period=day\|week\|month`, padrão `month`. |
| `GET /dashboard/weekly-revenue` | Autenticado; últimos sete dias. |
| `GET /dashboard/alerts` | Autenticado; aniversários, Platinum e estoque conforme papel. |
| `GET /dashboard/upcoming` | Autenticado; `days=2`, entre 1 e 7. |
| `GET /reports/revenue` | A/G; `period_start`, `period_end`, `professional_id`, `category_id`. |
| `GET /reports/clients` | A/G; `period_start`, `period_end`. |
| `GET /reports/loyalty-monthly` | A/G; `months=6`, entre 1 e 24. |
| `GET /reports/referrals-monthly` | A/G; `months=6`, entre 1 e 24. |
| `GET /audit-logs` | A/G; `user_id`, `action`, `limit=100`, `offset=0`. |

Nas listas paginadas de clientes, agenda, fidelidade e indicações, `limit` aceita de 1 a 200 e `offset` não pode ser negativo. Auditoria aceita até 500 por página. As demais listas não oferecem paginação geral: não pressuponha que todos os módulos tenham o mesmo contrato.

### Erros e limites de requisições

Erros usuais: **400** requisição/link inválido; **401** sessão inválida/expirada; **402** assinatura necessária; **403** papel/escopo insuficiente; **404** recurso não encontrado no escopo; **409** conflito; **422** validação; **429** limite de requisições; **502/503** serviço externo ou configuração indisponível. `detail` pode ser texto, objeto ou lista de validação.

| Operação | Limite atual |
|---|---|
| Login | 5 tentativas por IP/e-mail em 5 minutos; 30 por IP em 5 minutos. Tentativas bem-sucedidas também são registradas. |
| Cadastro de salão | 5 por IP por hora. |
| Solicitar recuperação | 5 por IP em 15 minutos; 3 por e-mail por hora. |
| Redefinir senha | 10 por IP em 15 minutos. |
| Criar cliente ou agendamento | 30 por usuário por minuto, em limitadores separados. |
| Abrir Checkout/Portal | 10 por usuário por minuto, cota compartilhada. |
| Exportar salão | 3 por usuário por hora. |

429 inclui `Retry-After`. Os contadores são locais ao processo e reiniciam com a API. A identificação correta do IP depende da configuração de proxy descrita no guia de produção.

## 6. Dados e manutenção

| Tabela | Conteúdo |
|---|---|
| `tenants` | Salão, disponibilidade, prazos de assinatura, vínculos Stripe e aceite dos termos. |
| `users` | Identidade, hash da senha, papel, vínculo profissional e versão de sessão. |
| `clients`, `professionals` | Cadastro e informações operacionais do salão. |
| `service_categories`, `services`, `service_recipes` | Catálogo e consumo previsto. |
| `appointments` | Agenda, conclusão, pagamentos registrados, fotos e lembrete. |
| `products`, `stock_movements` | Insumos e histórico de saldo. |
| `loyalty_transactions`, `referrals` | Pontos e conversões de indicação. |
| `audit_logs` | Metadados de mutações HTTP e operações de suporte. |
| `password_reset_tokens` | Hashes de tokens de recuperação, expiração e uso. |
| `billing_webhook_events` | Identificadores dos eventos Stripe já processados. |

Os registros operacionais possuem `tenant_id`. [database.py](database.py) impõe escopo de sessão, valida escrita e restringe consultas privilegiadas; [models/__init__.py](models/__init__.py) e as migrações incluem restrições compostas para referências do mesmo salão. E-mail de usuário permanece globalmente único.

Use Alembic para evoluir o schema e valide migrações em banco descartável. Antes de atualizar produção, produza backup consistente de banco **e** fotos e ensaie a restauração conforme [PRODUCTION.md](PRODUCTION.md). Exportação de um salão não substitui backup completo.

## 7. Verificação e solução de problemas

Os comandos de teste estão no [README](README.md) e em [CLAUDE.md](CLAUDE.md). A definição executável da validação contínua é [.github/workflows/ci.yml](.github/workflows/ci.yml): backend, frontend, migrações SQLite/PostgreSQL, auditoria de dependências, containers e restauração. Testes PostgreSQL são ignorados quando `TEST_POSTGRES_URL` não está configurada; um resultado SQLite não comprova essa etapa.

| Sintoma | Verificação recomendada |
|---|---|
| Backend não inicia | Confira `SECRET_KEY`, dependências, `APP_ENV` e mensagem de validação. Em produção confira migrações e se já existe uma API com o lock do banco. |
| Frontend não encontra a API | Confira o proxy `/api`, endereço/porta do backend e `VITE_API_URL` usado no build. |
| Login retorna 401 | Confira e-mail/senha e se usuário/salão estão ativos. Uma API fora do ar provoca falha de conexão, não um diagnóstico confiável de senha incorreta. |
| Acesso redireciona para assinatura | Consulte `/billing/status`; verifique vencimento, cobrança e entrega/reprocessamento de webhooks. |
| Recuperação retorna 503 | Configure e homologue SMTP. Um pedido aceito não comprova que a mensagem chegou à caixa de entrada. |
| Coluna/tabela ausente | Confira a revisão com `python -m alembic current` e aplique a migração prevista. Não execute seed para corrigir schema. |
| Ambiente virtual copiado não executa | Crie um ambiente virtual novo no destino e reinstale pelos requirements. Não remova o banco para corrigir Python. |
| Foto retorna 404/403 | Confira a referência no atendimento do mesmo salão, a autorização do usuário e o volume persistente. |
| Horários divergentes | Confira o fuso operacional do servidor/Compose e a convenção de datas da integração; não há configuração individual por salão. |

Limites operacionais e tarefas de ativação comercial permanecem registrados em [PRODUCTION.md](PRODUCTION.md). Para política de segurança e relato de vulnerabilidades, consulte [SECURITY.md](SECURITY.md).
