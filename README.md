# Velour — gestão de salões como SaaS

Agenda, clientes, profissionais, serviços, estoque, fidelidade, indicações e relatórios. React + TypeScript no frontend, FastAPI no backend, PostgreSQL 17 em produção e SQLite no desenvolvimento.

O SaaS inclui isolamento por salão, cadastro com 14 dias de teste, assinatura mensal via Stripe Checkout/Portal, webhooks assinados, recuperação de senha por e-mail e exportação dos dados do salão. Para abrir vendas, configure e homologue domínio/HTTPS, Stripe, SMTP, documentos da empresa, backups externos e monitoramento conforme o [guia de produção](PRODUCTION.md).

## Executar localmente

Requisitos: Python 3.12 ou 3.13 e Node.js 24 com npm. Execute na raiz do repositório:

```sh
python -m venv .venv
```

Ative o ambiente e copie a configuração de exemplo. No PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

No Linux/macOS:

```sh
. .venv/bin/activate
cp .env.example .env
```

Em uma instalação nova, edite `.env`: gere `SECRET_KEY` com o comando abaixo; mantenha `APP_ENV=development`, `DATABASE_URL=sqlite:///./velour.db`, `AUTO_CREATE_TABLES=false`, `APP_URL=http://localhost:5173` e `CORS_ORIGINS=http://localhost:5173`. Não substitua um `.env` existente sem preservar sua configuração.

```sh
python -c "import secrets; print(secrets.token_hex(32))"
python -m pip install -r requirements-dev.txt
alembic upgrade head
python bootstrap_admin.py
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

O bootstrap solicita nome, e-mail e senha do administrador e cria ou reutiliza o salão configurado por `BOOTSTRAP_TENANT_SLUG` (padrão `legacy`). Não há senha padrão. Em outro terminal:

```sh
cd frontend
npm ci
npm run dev
```

Abra `http://localhost:5173`; Vite encaminha `/api` para `http://127.0.0.1:8000`. A documentação interativa da API local fica em `http://127.0.0.1:8000/docs`.

Para testar o cadastro público, defina `SIGNUP_ENABLED=true` e URLs HTTPS em `TERMS_URL` e `PRIVACY_URL`: a tela exige esses links mesmo no desenvolvimento. Para desenvolver com cadastro fechado, use o bootstrap. `seed.py` cria dados de demonstração com credenciais públicas e só pode ser usado em um banco descartável de desenvolvimento. `start.bat` é apenas um atalho local, depois da instalação e das migrações.

## Testar

Use um ambiente e bancos de teste, sem dados comerciais. No PowerShell, antes do backend:

```powershell
$env:APP_ENV = 'test'
$env:SECRET_KEY = 'test-only-secret-key-do-not-use-in-production'
$env:SCHEDULER_ENABLED = 'false'
$env:AUTO_CREATE_TABLES = 'false'
$env:DATABASE_URL = 'sqlite:///./validation.db'
python -m pytest tests/ -q
alembic upgrade head
alembic check
```

No Linux/macOS, use `export APP_ENV=test`, `export SECRET_KEY='test-only-secret-key-do-not-use-in-production'`, `export SCHEDULER_ENABLED=false`, `export AUTO_CREATE_TABLES=false` e `export DATABASE_URL=sqlite:///./validation.db` antes dos mesmos comandos Python/Alembic. Abra outro terminal sem essas variáveis para retomar o desenvolvimento.

No diretório `frontend`:

```sh
npm run lint
npm run test
npm run build
npm audit --audit-level=high
```

As fixtures comuns usam SQLite temporário. Os testes PostgreSQL exigem `TEST_POSTGRES_URL` apontando para um banco **descartável**, previamente migrado. A [CI](.github/workflows/ci.yml) executa backend, frontend, auditoria de dependências, migrações, PostgreSQL real, restauração em outro banco e inicialização/backup dos containers. Um teste que foi ignorado localmente não equivale a aprovação em PostgreSQL.

## Operação do SaaS

| Capacidade | Comportamento |
| --- | --- |
| Conta | Um salão por usuário; e-mail único na plataforma |
| Acesso | Administrador, gerente e profissional com permissões de servidor |
| Teste | 14 dias sem cartão no cadastro |
| Assinatura | Um Price mensal do Stripe por implantação, quantidade 1 |
| Vencimento | Bloqueia operações de negócio; preserva login, cobrança, exportação do administrador e fotos autorizadas enquanto a conta estiver ativa |
| Sessão | Token em `sessionStorage`, validado contra usuário e salão no servidor |
| Exportação | JSON por salão, sem hashes de senha ou tokens; fotos como referências autenticadas |
| Infraestrutura | Uma API com um worker, PostgreSQL e volumes de dados/fotos |
| Horários | Um fuso operacional por implantação; `SALON_TIMEZONE` no Compose, padrão `America/Sao_Paulo` |

O lock exclusivo no PostgreSQL recusa uma segunda API. Esta versão não oferece alta disponibilidade, várias contas por usuário, eliminação automática de dados nem emissão fiscal. Suspensão de conta, solicitações de privacidade e retenção de backups exigem operação assistida. Termos e política abaixo são minutas com campos empresariais pendentes.

## Documentação

- [Manual funcional e referência da API](DOCUMENTACAO.md)
- [Implantação, cobrança, backup e homologação](PRODUCTION.md)
- [Arquitetura e isolamento por salão](MULTI_TENANCY_PLAN.md)
- [Cadastro, assinatura e estados de acesso](ONBOARDING_BILLING_PLAN.md)
- [Desenvolvimento e convenções do repositório](CLAUDE.md)
- [Segurança e relato de vulnerabilidades](SECURITY.md)
- [Minuta dos Termos de Uso](TERMOS_DE_USO.md)
- [Minuta da Política de Privacidade](POLITICA_DE_PRIVACIDADE.md)

Os nomes dos dois arquivos terminados em `_PLAN.md` foram preservados para manter links existentes; seu conteúdo descreve a implementação atual e seus limites.
