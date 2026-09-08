# Orientações para colaboradores e agentes

O Velour é um SaaS de gestão de salões, com React/TypeScript em `frontend/` e FastAPI/SQLAlchemy na raiz. Cada salão possui seu próprio escopo de dados e assinatura. Leia [README.md](README.md) para instalação, [DOCUMENTACAO.md](DOCUMENTACAO.md) para contratos e regras, [PRODUCTION.md](PRODUCTION.md) para operação e [SECURITY.md](SECURITY.md) para segurança.

Não descreva funcionalidades implementadas como pendências de arquitetura nem confunda uma suíte verde com produção comercial homologada. Registre quais verificações foram realmente executadas e quais dependem de infraestrutura ou credenciais externas.

## Ambiente local

A CI utiliza Python 3.12/3.13 e Node.js 24. As dependências Python estão em `requirements.txt` e `requirements-dev.txt`; o frontend usa `package-lock.json`. Instale com `python -m pip install -r requirements-dev.txt` e, em `frontend/`, `npm ci`.

Crie um ambiente virtual novo na raiz:

```text
python -m venv .venv
```

Ativação em **PowerShell**:

```powershell
.\.venv\Scripts\Activate.ps1
```

Ativação em **bash/zsh**:

```bash
source .venv/bin/activate
```

No `cmd.exe`, use `.venv\Scripts\activate.bat`. Se a política do PowerShell impedir ativação, execute diretamente `.\.venv\Scripts\python.exe`; não altere a política global da máquina para rodar o projeto.

Se `.env` ainda não existir, copie `.env.example` e configure um segredo aleatório. Não sobrescreva `.env` existente nem leia/exiba seus segredos no relatório. `config.py` carrega esse arquivo e também respeita variáveis de ambiente do processo. `SECRET_KEY` é exigida já na importação; não há fallback de código.

Para uma instalação nova, configure `AUTO_CREATE_TABLES=false` e execute na raiz:

```text
python -m alembic upgrade head
```

Crie a primeira conta pelo cadastro público quando deliberadamente habilitado (`SIGNUP_ENABLED=true`) ou por `python bootstrap_admin.py`, que solicita os dados sem exigir senha em argumento. O cadastro do `.env.example` começa fechado. `seed.py` é opcional e destrutivo para os dados do salão `demo`; não é migração nem etapa obrigatória e só pode rodar em desenvolvimento.

Em dois terminais, inicie:

```text
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

```text
cd frontend
npm run dev
```

Frontend: `http://localhost:5173`. API de desenvolvimento: `http://127.0.0.1:8000/docs`. A aplicação usa `/api` e o proxy Vite; `VITE_API_URL` permite configurar outra base no build. Não introduza endereços fixos nas páginas.

## Organização e responsabilidades

| Local | Responsabilidade |
|---|---|
| `frontend/src/api/client.ts` | Cliente Axios, contratos por domínio, Bearer, tratamento de 401/402 e downloads privados. Use estes clientes nas páginas. |
| `frontend/src/api/types.ts` | Tipos que acompanham schemas e enums Python. |
| `frontend/src/context/` | Sessão em `sessionStorage`, validação via `/auth/me`, login/cadastro/logout. |
| `frontend/src/pages/`, `components/` | Rotas e componentes de interface, incluindo autenticação, cobrança e fotos privadas. |
| `main.py`, `config.py` | Configuração, ciclo de vida, middlewares, healthcheck, inclusão das rotas e bloqueio de negócio por assinatura. |
| `database.py`, `models/` | Sessões com isolamento por salão, entidades, valores decimais e restrições de banco. |
| `routers/`, `schemas/` | Autorização, contratos HTTP e transações de negócio. |
| `auth.py`, `routers/account_recovery.py` | Hash de senha, JWT, papéis, revogação e tokens de recuperação de uso único. |
| `routers/tenants.py`, `routers/billing.py` | Cadastro, exportação, teste, Checkout/Portal e sincronização Stripe. |
| `domain_locks.py`, `runtime_guard.py`, `rate_limit.py` | Serialização local, exclusividade da API em produção e limites atômicos de requisição. |
| `birthday_scheduler.py`, `reminder_scheduler.py` | Bônus às 08h e lembretes a cada hora, conforme fuso operacional. |
| `email_service.py`, `account_email.py` | SMTP para atendimento e recuperação; não há fila durável de mensagens. |
| `audit.py`, `request_logging.py`, `logging_config.py` | Auditoria e logs estruturados sem payloads ou credenciais. |
| `migrations/`, `alembic.ini` | Evolução versionada do schema. |
| `preflight.py`, `platform_admin.py`, `scripts/backup.py` | Verificação de implantação, suporte local e backup consistente. |
| `compose.yaml`, `compose.production.yaml`, `deploy/` | PostgreSQL, migração, API única, frontend e HTTPS. |

## Invariantes de segurança e dados

- Toda consulta operacional usa `get_db`/`ScopedSession` com `tenant_scope` definido pela autenticação, não por `tenant_id` fornecido pelo cliente. Novas entidades operacionais devem herdar `TenantScoped` e ter migração com as restrições aplicáveis.
- `system_scope`/`system_session` são exceções para autenticação, cobrança e manutenção confiável. Não os use para contornar uma falha de isolamento em uma rota de negócio. SQL bruto, Core e operações bulk privilegiadas exigem análise explícita de escopo.
- Referências entre entidades precisam pertencer ao mesmo salão. Teste acesso a IDs e fotos de outro salão, consultas, gravações, relações e reutilização do identity map quando alterar persistência.
- `require_admin` e `require_manager` aceitam admin/manager. Gestão de cobrança, exportação e alteração de administradores exigem admin. Professional exige vínculo válido e só pode operar seus atendimentos; não remova `ensure_professional_scope`. Listas também devem preservar esse escopo: profissionais recebem apenas o próprio perfil e transações de fidelidade de clientes vinculados por agendamento.
- A dependência de assinatura é aplicada às rotas de negócio em `main.py`. Login, recuperação, cobrança, exportação e leitura autorizada de fotos permanecem fora desse bloqueio. Salão desativado não autentica.
- O JWT identifica salão e usuário, mas papel/estado são verificados no banco. Preserve `token_version` e sua revogação em recuperação e mudanças de acesso. Logout do navegador não constitui revogação global.
- Mantenha segredos somente no servidor. Variáveis `VITE_*` são públicas no bundle. Não persista tokens em `localStorage`, não registre token de recuperação nem exponha `/uploads` como diretório estático.
- Upload de atendimento aceita JPEG/PNG/WebP por assinatura do conteúdo, até 5 MiB. A referência deve pertencer a um atendimento acessível; URLs arbitrárias não podem transferir autorização sobre fotos.
- Produção exige PostgreSQL, migrações e uma réplica/worker. Não aumente `--workers`, execute outra API ou duplique agendadores sem redesenhar locks, rate limiting e jobs; o advisory lock deve impedir esse cenário.
- Não registre senhas, hashes, tokens, corpo de requisição, query string de recuperação, cabeçalhos de autenticação, fotos ou dados clínicos em logs. Preserve os middlewares e as configurações de proxy que evitam essa exposição.

## Regras de domínio a preservar

- O servidor calcula `ends_at` usando a duração do serviço. Conflitos ignoram `cancelled`/`no_show`; horários adjacentes são válidos.
- Concluir atendimento é uma transação única: cobrança, descontos, pontos, tier, indicação e consumo de estoque. Repetir conclusão não pode repetir efeitos. Encerrados não devem ser reabertos via status.
- Use `Decimal` para dinheiro e respeite as casas decimais dos schemas. `schemas/numbers.py` fornece `JsonDecimal` para produzir números nas respostas JSON sem trocar os valores internos por float. Não trate zero como valor ausente. A comissão é uma fração de 0 a 1.
- Desconto usa o tier antes do atendimento; resgate é múltiplo de 100 e limitado pelo saldo. Tier mais pontos não excedem 50% do valor base. Todos os pontos solicitados são debitados mesmo quando o teto reduz o desconto.
- O primeiro atendimento do indicado converte a indicação (+150/+75). O bônus de aniversário é de 100 e consulta o histórico para evitar duplicação no mês.
- `paid=true` exige `amount_paid` e `payment_method`. Pagamento do atendimento é um registro operacional separado da assinatura Stripe.
- Fotos novas entram pelo endpoint multipart. Os campos de URL na conclusão só podem repetir referências já existentes naquele atendimento.
- Consumo de estoque pode deixar saldo negativo e sempre gera movimento; perda manual acima do saldo é rejeitada. PATCH de produto não altera saldo. PUT de receita substitui a lista inteira.
- Datas da agenda são horários locais sem fuso; `scheduled_at` e os filtros da agenda rejeitam `Z`/offset com 422. Preserve o texto do formulário `datetime-local`, sem `toISOString`. Prazos SaaS/recuperação usam UTC: não aplique conversões genéricas a ambos. A implantação usa um fuso operacional compartilhado por todos os salões. A correção não reinterpreta datas históricas sem offset armazenado.
- Categorias vinculadas a serviços, inclusive inativos, não podem ser excluídas (409). Alterar a categoria de um serviço exige que a nova categoria exista no mesmo salão.
- Stripe é a autoridade da assinatura. Preserve verificação da assinatura do webhook, ambiente, cliente, tenant, Price e quantidade; consulte estado atual no provedor antes de aplicar. Repetições, eventos fora de ordem e falha do provedor não devem conceder acesso indevido ou criar cobranças duplicadas.
- Desativação e cancelamento não apagam histórico. Exportação JSON não inclui os arquivos de foto nem substitui backup.

Mantenha enums e schemas sincronizados com o frontend: papéis `admin/manager/professional`; gêneros `M/F/other`; conversa `chatty/quiet/neutral`; agenda `scheduled/confirmed/in_progress/completed/cancelled/no_show`; pagamento `cash/debit_card/credit_card/pix/other`; fidelidade `earned_appointment/earned_referral/earned_birthday/redeemed`.

## Verificação antes da entrega

Use ambiente de teste e banco descartável. Não execute testes ou ensaios de migração contra a base de clientes. Para testes locais, defina as variáveis **antes** de importar módulos Python; não reutilize a configuração de produção do `.env`.

PowerShell, na raiz e com o ambiente virtual ativado:

```powershell
$env:APP_ENV = 'test'
$env:SECRET_KEY = python -c 'import secrets; print(secrets.token_hex(32))'
$env:DATABASE_URL = 'sqlite:///:memory:'
$env:AUTO_CREATE_TABLES = 'false'
$env:SCHEDULER_ENABLED = 'false'
python -m pytest tests/ -v
```

Bash/zsh equivalente:

```bash
export APP_ENV=test
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export DATABASE_URL='sqlite:///:memory:'
export AUTO_CREATE_TABLES=false
export SCHEDULER_ENABLED=false
python -m pytest tests/ -v
```

Em `frontend/`:

```text
npm ci
npm run lint
npm run test
npm run build
npm audit --audit-level=high
```

Auditoria Python de runtime:

```text
python -m pip install pip-audit==2.10.1
python -m pip_audit -r requirements.txt
```

Para mudanças de schema, configure `DATABASE_URL` para um banco descartável novo, mantendo `AUTO_CREATE_TABLES=false`, e execute:

```text
python -m alembic upgrade head
python -m alembic check
```

Teste migração de base existente quando pertinente, além de banco vazio. A migração SaaS tem restrições próprias de downgrade; leia seu código, não suponha que `downgrade base` seja reversível em qualquer revisão. Não use `seed.py`, `create_all` ou `alembic stamp` para esconder divergência de schema.

Para validar PostgreSQL, crie/migre uma base de teste e defina `TEST_POSTGRES_URL` para essa base antes de executar:

```text
python -m pytest tests/test_postgres_tenancy.py -v
```

Sem `TEST_POSTGRES_URL`, essa suíte é ignorada. Quando alterar consultas, também valide os endpoints afetados em PostgreSQL: testes SQLite não demonstram compatibilidade de funções SQL específicas.

A [.github/workflows/ci.yml](.github/workflows/ci.yml) contém as etapas completas de migração, PostgreSQL, inicialização dos containers, backup e restauração. A homologação de produção e o preflight estão em [PRODUCTION.md](PRODUCTION.md). Relate testes pulados, falhas e limitações; não mantenha contagens fixas de testes neste documento.

Ao concluir uma alteração, atualize os Markdown e contratos afetados, confira os links relativos e o diff, e reporte resultado e verificações. Nunca inclua `.env`, banco local, fotos, dumps, tokens ou dados reais de clientes no commit.
