# Velour — gestão de salões como SaaS

React + TypeScript e FastAPI, com PostgreSQL em produção e SQLite para desenvolvimento. Agenda, clientes, profissionais, serviços, estoque, fidelidade, indicações e relatórios.

## Preparação comercial

O núcleo SaaS está implementado: isolamento de registros por salão, cadastro de administrador e trial de 14 dias, Stripe Checkout/Portal, webhook assinado e idempotente, controle de acesso por assinatura, recuperação de senha com tokens de uso único, exportação e operação assistida de contas.

**Para liberar vendas:** configure domínio/HTTPS, Stripe e preço mensal, SMTP, documentos reais da empresa, backups externos e alertas; complete os testes de homologação do [guia de produção](PRODUCTION.md). A implementação não constitui garantia de segurança absoluta, auditoria externa ou conformidade jurídica. Os documentos de termos/privacidade do repositório são rascunhos.

A topologia suportada é uma API com **um worker** e PostgreSQL. Um lock do banco recusa instâncias adicionais; não há alta disponibilidade nesta versão. O e-mail de usuário é único na plataforma. Cada implantação usa um único fuso operacional, configurável por `SALON_TIMEZONE` no Compose (padrão America/Sao_Paulo).

## Desenvolvimento

Python 3.12/3.13 e Node.js 24:

```sh
python -m venv .venv
# Ative .venv conforme seu sistema operacional.
python -m pip install -r requirements-dev.txt
# Copie .env.example para .env e gere uma SECRET_KEY própria.
alembic upgrade head
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Em outro terminal:

```sh
cd frontend
npm ci
npm run dev
```

Abra `http://localhost:5173`. Vite encaminha `/api` para a API local. Para cadastro pela interface, habilite `SIGNUP_ENABLED=true` e informe URLs HTTPS de termos/privacidade do seu ambiente de teste. Para operação assistida, use `python bootstrap_admin.py`. `seed.py` é exclusivo para desenvolvimento e cria usuários de demonstração com credenciais públicas; nunca execute em produção.

## Testes e validação

```sh
python -m pytest tests/ -q
alembic check
cd frontend
npm run lint
npm run test
npm run build
npm audit --audit-level=high
```

Defina `SECRET_KEY` de teste antes de rodar pytest. Os testes unitários/API usam bancos temporários. `tests/test_postgres_tenancy.py` só roda quando `TEST_POSTGRES_URL` aponta para um banco PostgreSQL **de testes**, migrado com Alembic. A CI executa isolamento sobre PostgreSQL 17, restauração em um segundo banco, build/boot dos containers e backup consistente. Não use banco comercial em testes.

## Fluxos SaaS

| Endpoint | Uso |
| --- | --- |
| `GET /tenants/signup-config` | Configuração pública de cadastro/documentos |
| `POST /tenants/signup` | Salão e administrador em transação única |
| `POST /auth/login`, `GET /auth/me` | Sessão validada por usuário e salão |
| `POST /auth/forgot-password`, `/auth/reset-password` | Recuperação por e-mail e revogação de sessões |
| `GET /billing/status` | Trial, assinatura e acesso efetivo |
| `POST /billing/checkout-session` | Assinatura no Checkout hospedado |
| `POST /billing/portal-session` | Pagamento/cancelamento no portal do Stripe |
| `POST /billing/webhook` | Sincronização autenticada pela assinatura Stripe |
| `GET /tenants/export` | Exportação de registros, somente administrador |
| `GET /uploads/{filename}` | Foto vinculada a atendimento autorizado |
| `GET /health` | Disponibilidade da API/banco |

As rotas de negócio exigem assinatura ativa ou trial válido. Após expiração, o titular conserva login, cobrança, exportação e acesso autorizado às fotos enquanto a conta não estiver suspensa. Os preços e datas de cobrança são apresentados pelo Stripe antes da confirmação. Senhas e chaves nunca são enviadas à SPA como dados de conta; o token de acesso fica no sessionStorage e é validado no servidor.

## Documentação

- [Implantação, Stripe, backup e homologação](PRODUCTION.md)
- [Histórico da arquitetura multi-tenant](MULTI_TENANCY_PLAN.md)
- [Histórico do plano de onboarding/billing](ONBOARDING_BILLING_PLAN.md)
- [Documentação funcional anterior](DOCUMENTACAO.md)
- [Política de segurança](SECURITY.md)

Os planos históricos descrevem decisões anteriores; detalhes atuais de operação e limitações estão em `PRODUCTION.md` e nos testes executáveis.
