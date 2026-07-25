# Velour — Documentação Completa do Sistema

Sistema de gestão interno para salão de beleza premium. Uso exclusivo de **profissionais e gestores** (não há acesso do cliente final). O diferencial é o **briefing pré-atendimento**: o profissional abre a agenda e já sabe tudo sobre o cliente antes dele sentar na cadeira.

---

## Índice

1. [Visão geral e arquitetura](#1-visão-geral-e-arquitetura)
2. [Como iniciar o sistema](#2-como-iniciar-o-sistema)
3. [Login e papéis de acesso](#3-login-e-papéis-de-acesso)
4. [Módulos e ações (tela a tela)](#4-módulos-e-ações-tela-a-tela)
5. [Regras de negócio](#5-regras-de-negócio)
6. [Referência da API (todos os endpoints)](#6-referência-da-api-todos-os-endpoints)
7. [Modelo de dados](#7-modelo-de-dados)
8. [Segurança](#8-segurança)
9. [Estrutura de arquivos](#9-estrutura-de-arquivos)
10. [Solução de problemas](#10-solução-de-problemas)

---

## 1. Visão geral e arquitetura

```
Navegador ↔ React SPA (Vite, porta 5173) ↔ FastAPI (Python, porta 8000) ↔ SQLite (velour.db)
```

| Camada | Tecnologia |
|---|---|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS |
| Backend | FastAPI (Python) + SQLAlchemy ORM |
| Banco | SQLite (`velour.db`) |
| Autenticação | JWT (HS256) + senha PBKDF2-HMAC-SHA256 |
| Agendador | APScheduler (bônus de aniversário às 08h) |

Toda a **regra de negócio fica no servidor**. O frontend nunca calcula desconto, tier ou pontos de forma autoritativa — só exibe e envia. Operações complexas (concluir atendimento) são **atômicas**: ou tudo grava, ou nada (rollback).

---

## 2. Como iniciar o sistema

### Modo rápido (1 clique)
Dê duplo-clique em **`start.bat`** (ou rode `.\start.bat` no terminal). Ele abre duas janelas: backend (8000) e frontend (5173).

### Modo manual (dois terminais)

**Terminal 1 — Backend:**
```powershell
.\.venv\Scripts\activate
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```

Depois abra **http://localhost:5173**. A documentação interativa da API fica em **http://127.0.0.1:8000/docs** (Swagger).

> **Importante:** sempre use `python -m uvicorn` e `python -m pip` (e não `uvicorn`/`pip` direto), porque os atalhos `.exe` da `.venv` desta máquina apontam para um caminho antigo.

### Popular o banco (primeira vez ou para resetar)
```powershell
python seed.py
```
Cria dados de desenvolvimento realistas (2 usuários, 4 profissionais, 15 serviços, 7 insumos, 20 clientes, 30 agendamentos, indicações e transações).

---

## 3. Login e papéis de acesso

**Credenciais de desenvolvimento:**
- Admin: `admin@velour.com` / `velour2026`
- Gerente: `gerente@velour.com` / `velour2026`

O token JWT vale **8 horas** e fica no `localStorage` do navegador. Um interceptor do Axios injeta o `Bearer <token>` em toda requisição. Se o token expira (401), o app desloga e volta pro login automaticamente.

| Papel | Permissões |
|---|---|
| **admin** | Acesso total, incluindo cadastro de usuários, profissionais, serviços, insumos e exclusões. |
| **manager** (gerente) | Mesmas permissões administrativas do admin (ambos passam pela checagem `require_admin`). |
| **professional** | Usuário autenticado comum: lê e opera, mas não acessa rotas restritas a admin. |

Rotas marcadas como "requer admin" exigem papel admin **ou** manager.

---

## 4. Módulos e ações (tela a tela)

### 4.1 Dashboard (`/`)
Tela inicial após o login. Mostra:
- **KPIs do dia:** agendamentos de hoje, receita de hoje, clientes ativos, pontos emitidos hoje.
- **Gráfico de receita** dos últimos 7 dias (barras).
- **Card de Alertas:**
  - 🎂 Aniversariantes do dia
  - 👑 Clientes Platinum agendados hoje
  - ⚠️ **Estoque baixo** (insumos no/abaixo do mínimo)
  - 🗓️ **Vencendo em breve** (insumos com validade em até 30 dias, ou já vencidos)
- **Status breakdown:** contagem de agendamentos por status.
- **Agenda de hoje:** tabela com horário, cliente (+ tier), profissional, serviço, status.
- **Ação "Briefing":** clicar abre o painel lateral com o perfil completo do cliente (preferências, alergias, último atendimento, fidelidade).

### 4.2 Clientes (`/clients`)
- **Lista** com código VLR, nome, tier, telefone, visitas, total gasto, pontos.
- **Filtros:** por tier, por gênero, por inatividade (sem agendar há X dias).
- **Criar cliente:** nome, telefone, email, gênero, nascimento, perfil sensorial (bebida, música, temperatura, preferência de conversa), alergias, observações, e código de indicação de quem o indicou.
  - Ao cadastrar: gera automaticamente o **código VLR** sequencial (`VLR-00001`) e um **código de indicação** único de 8 caracteres.
- **Editar cliente:** todos os campos acima.
- **Perfil do cliente** (`/clients/{id}`): visão geral, perfil sensorial, fidelidade (tier, pontos, progresso para o próximo tier), histórico e indicações.
- **Desativar (soft-delete):** marca `is_active = false` (requer admin). O cliente some das listas mas o histórico é preservado.

### 4.3 Agendamentos (`/appointments`)
- **Lista** com filtros por status, data e busca por cliente/profissional/serviço. Cada linha mostra horário, cliente (+ tier), serviço, profissional, preço e status.
- **Novo agendamento:** seleciona cliente, profissional, serviço, data/horário, ocasião e observações.
  - O servidor calcula o `ends_at` (= início + duração do serviço).
  - **Detecção de conflito:** se o profissional já tem agendamento sobreposto, retorna **HTTP 409** e o app avisa. Cancelados e no-show são ignorados.
- **Mudar status:** confirmar, iniciar, marcar não-compareceu, etc. (Não aceita "concluído" por aqui — concluir tem fluxo próprio.)
- **Concluir atendimento** (modal): a ação mais rica do sistema. Numa única transação atômica:
  1. Recebe o **valor cobrado**, pontos a resgatar, fórmula usada, observações e fotos antes/depois.
  2. Aplica o **desconto automático por tier** (ver regras) sobre o valor base.
  3. Aplica o **resgate de pontos** (depois do tier, respeitando o teto combinado de 50%).
  4. Mostra o **resumo de descontos**: valor base → desconto do tier (%) → resgate → valor final.
  5. **Ajuste de insumos (ficha técnica):** lista os insumos que o serviço consome e permite ajustar a dosagem real usada.
  6. **Dá baixa no estoque** dos insumos consumidos (com os ajustes), registrando no ledger.
  7. Credita os **pontos ganhos**, atualiza `total_spent`, `total_visits` e **recalcula o tier**.
  8. Se for o primeiro atendimento concluído de um cliente indicado, **converte a indicação** (+150 pts a quem indicou, +75 ao indicado).
  9. Grava `tier_at_service` e `tier_discount_amount` no agendamento (para relatórios).
- **Cancelar:** muda o status para `cancelled` (não exclui).
- **Upload de fotos:** envia foto antes/depois; o tipo é validado pelo conteúdo real do arquivo (magic bytes), não pela extensão/header enviado. As fotos ficam atrás de um endpoint autenticado (`GET /uploads/{filename}`), não são públicas.

### 4.4 Profissionais (`/professionals`)
- **Lista** em cards: nome, especialidade, comissão, e estatísticas do mês (atendimentos, receita, comissão, top serviço).
- **Novo / Editar profissional:** nome, telefone, email, gênero, especialidade, bio, **taxa de comissão** (%) e **meta financeira do mês** (R$).
- **Painel do profissional** (botão 🎚️): abre um painel com:
  - **Progresso da meta do mês:** barra com receita realizada vs. meta, % atingido, quanto falta e comissão acumulada.
  - **Clientes a recuperar:** clientes daquele profissional que ultrapassaram a própria **cadência histórica** de retorno (média de dias entre visitas), ordenados pelos mais atrasados. Exige ≥2 atendimentos para haver média.
- **Ativar/desativar** (soft-delete, requer admin).

### 4.5 Serviços (`/services`)
- **Aba Serviços:** tabela com nome, categoria, duração, preço, pontos, status. Criar/editar serviço (requer admin para criar/editar/excluir).
- **Aba Categorias:** cards com ícone, público-alvo (M/F/todos) e nº de serviços. Criar categoria.
- **Ficha técnica** (botão 🧪 por serviço): editor da receita de insumos — define quais insumos e quantas unidades cada execução consome. É o que dispara a **baixa automática de estoque** ao concluir o atendimento.

### 4.6 Estoque (`/inventory`)
- **Lista de insumos:** nome, saldo (vermelho se ≤ mínimo), estoque mínimo, validade (âmbar se ≤ 30 dias), custo por unidade. Filtro "só abaixo do mínimo".
- **Novo / Editar insumo:** nome, unidade (ml / g / unidade), saldo inicial, estoque mínimo, validade, custo por unidade.
  - O saldo só muda por **movimentações** — o campo de saldo não é editável direto, garantindo histórico íntegro.
- **Movimentar estoque** (botão ➕): registra entrada (compra), perda/descarte ou ajuste, com preview do novo saldo. Cada movimentação vira uma linha no ledger.
- **Histórico** (botão 🕐): lista todas as movimentações do insumo (entradas, consumos por atendimento, perdas, ajustes) com saldo antes/depois.
- **Ativar/desativar** insumo.

### 4.7 Fidelidade (`/loyalty`)
- **Visão geral:** total de pontos em circulação, emitidos vs. resgatados no mês, distribuição de clientes por tier, top 10 por pontos.
- **Histórico de transações:** filtrável por cliente, tipo (ganho/resgate) e período.

### 4.8 Indicações (`/referrals`)
- **Tabela:** quem indicou → quem foi indicado → status (pendente/convertida) → pontos concedidos → data.
- **Ranking:** top 10 indicadores por número de conversões.
- A **conversão é automática** no primeiro atendimento concluído do indicado.

### 4.9 Relatórios (`/reports`)
- **Receita:** por período, profissional, categoria e gênero do cliente.
- **Clientes:** novos no período, risco de churn (sem voltar há 60+ dias), distribuição por tier.
- **Fidelidade mensal:** pontos emitidos vs. resgatados por mês.
- **Indicações mensais:** conversões e pontos investidos por mês.

### 4.10 Usuários (`/users`) — apenas admin/manager
- Lista de usuários do sistema, criar novo (nome, email, senha, papel) e editar (nome, papel, ativar/desativar).

---

## 5. Regras de negócio

### Pontos de fidelidade
- **Ganho:** `service.points_reward` se for > 0; senão `int(valor_final) × 1 ponto por R$1`.
- **Resgate:** 100 pts = R$10 de desconto; sempre em múltiplos de 100; os pontos são debitados integralmente mesmo que o desconto efetivo seja limitado pelo teto.

### Tiers de fidelidade (por `total_spent` acumulado)
| Tier | Faixa |
|---|---|
| Bronze | < R$500 |
| Silver | R$500 – R$1.499 |
| Gold | R$1.500 – R$2.999 |
| Platinum | ≥ R$3.000 |

Recalculado a cada atendimento concluído. **Sem downgrade automático.**

### Desconto automático por tier (aplicado ao concluir)
| Tier | Desconto |
|---|---|
| Bronze | 0% |
| Silver | 5% |
| Gold | 10% |
| Platinum | 15% |

Regras de combinação:
1. O desconto do tier é aplicado **primeiro**, sobre o valor base.
2. O resgate de pontos vem **depois**, limitado ao que sobra de um **teto absoluto de 50%** do valor base (tier + pontos nunca passam de 50%).
3. O tier usado é "fotografado" **antes** de o atendimento somar ao `total_spent` — quem sobe de tier nesse atendimento ainda paga com o desconto do tier anterior.
4. O tier e o valor descontado ficam gravados no agendamento (`tier_at_service`, `tier_discount_amount`).

### Conflito de horário
Rejeita com **HTTP 409** se, para o mesmo profissional, houver sobreposição:
`existente.início < novo.fim` **E** `existente.fim > novo.início`, ignorando `cancelled` e `no_show`.

### Conversão de indicação
No **primeiro atendimento concluído** do cliente indicado: a indicação pendente vira `converted`, +150 pts a quem indicou e +75 ao indicado, com transações de fidelidade registradas.

### Bônus de aniversário
`birthday_scheduler.py` roda **às 08h** (APScheduler): concede 100 pts aos aniversariantes do dia. É **idempotente** — não concede duas vezes no mesmo mês.

### Baixa automática de estoque (ficha técnica)
Ao concluir o atendimento, o sistema baixa do estoque os insumos da **ficha técnica** do serviço:
- A receita define a quantidade-padrão; os **overrides** do checkout substituem a dosagem real (e podem incluir insumos extras).
- `actual_qty = 0` ignora aquele insumo.
- A baixa é **incondicional** — a operação nunca trava no balcão. Se o saldo fica ≤ 0, o atendimento conclui normalmente e o **alerta de reposição** aparece no dashboard.
- Cada baixa registra uma movimentação no **ledger** (`stock_movements`), que é append-only (nunca sofre update/delete).

---

## 6. Referência da API (todos os endpoints)

> Base: `http://127.0.0.1:8000` · Documentação interativa: `/docs`

### Autenticação
```
POST /auth/login        form: { username, password } → { access_token, token_type, role, name }
GET  /auth/me           → dados do usuário autenticado
GET  /health            → { status: "ok", system: "Velour" }
```

### Usuários (requer admin)
```
GET    /users
POST   /users           { name, email, password, role }
PATCH  /users/{id}      { name?, role?, is_active? }
```

### Clientes
```
GET    /clients                 query: tier?, gender?, inactive_days?, limit, offset
GET    /clients/{id}
GET    /clients/{id}/briefing   perfil completo p/ pré-atendimento
POST   /clients
PATCH  /clients/{id}
DELETE /clients/{id}            soft-delete (admin)
```

### Profissionais
```
GET    /professionals               query: is_active?
GET    /professionals/{id}
GET    /professionals/{id}/stats    atendimentos, receita, comissão, ticket médio do mês
GET    /professionals/{id}/dashboard  meta do mês + clientes inativos por cadência
POST   /professionals               (admin)
PATCH  /professionals/{id}          (admin)
DELETE /professionals/{id}          soft-delete (admin)
```

### Serviços e categorias
```
GET    /service-categories
POST   /service-categories          (admin)
PATCH  /service-categories/{id}     (admin)
DELETE /service-categories/{id}     (admin)

GET    /services                    query: category_id?, is_active?
GET    /services/{id}
POST   /services                    (admin)
PATCH  /services/{id}               (admin)
DELETE /services/{id}               soft-delete (admin)
```

### Estoque / insumos
```
GET    /products                    query: is_active?, low_stock?
GET    /products/{id}
POST   /products                    (admin)
PATCH  /products/{id}               (admin) — saldo NÃO é editável aqui
DELETE /products/{id}               soft-delete (admin)
POST   /products/{id}/stock         (admin) entrada/perda/ajuste → gera movimentação
GET    /products/{id}/movements     histórico do ledger
```

### Ficha técnica (receita do serviço)
```
GET    /services/{id}/recipe        insumos consumidos pelo serviço
PUT    /services/{id}/recipe        (admin) substitui a ficha técnica inteira
```

### Agendamentos
```
GET    /appointments                query: date_from?, date_to?, status?, professional_id?, client_id?, limit, offset
GET    /appointments/{id}
POST   /appointments                calcula ends_at; 409 em caso de conflito
PATCH  /appointments/{id}/status    body: { status } — não aceita "completed"
POST   /appointments/{id}/complete  body: { price_charged, discount_points_used, formula_used, recipe_overrides[]? ... }
POST   /appointments/{id}/photos    multipart: photo_before?, photo_after?
DELETE /appointments/{id}           muda status p/ "cancelled"
```

### Fidelidade
```
GET    /loyalty/transactions        query: client_id?, type?, date_from?, date_to?
GET    /loyalty/overview            pontos em circulação, emitidos/resgatados, tiers, top 10
```

### Indicações
```
GET    /referrals                   query: status?, referrer_id?
GET    /referrals/ranking           top 10 indicadores por conversões
```

### Dashboard
```
GET    /dashboard/today             agenda + receita + breakdown do dia
GET    /dashboard/kpis              query: period=day|week|month
GET    /dashboard/weekly-revenue    últimos 7 dias
GET    /dashboard/alerts            aniversários, Platinum, estoque baixo, validade próxima
GET    /dashboard/upcoming          query: days=2 (1–7)
```

### Relatórios
```
GET    /reports/revenue             query: period_start?, period_end?, professional_id?, category_id?
GET    /reports/clients             query: period_start?, period_end?
GET    /reports/loyalty-monthly     query: months=6
GET    /reports/referrals-monthly   query: months=6
```

---

## 7. Modelo de dados

| Tabela | O que guarda |
|---|---|
| `users` | Gestores/profissionais do sistema (login, papel). |
| `clients` | Clientes: código VLR, perfil sensorial, alergias, fidelidade, indicação. |
| `professionals` | Profissionais: especialidade, comissão, **meta mensal**. |
| `service_categories` | Categorias de serviço (público-alvo, ícone). |
| `services` | Serviços: duração, preço, pontos. |
| `appointments` | Agendamentos: status, valores, **tier e desconto aplicados**, fórmula, fotos. |
| `loyalty_transactions` | Ledger de pontos (ganho/resgate). |
| `referrals` | Indicações (pendente/convertida). |
| `products` | **Insumos de estoque** (saldo, mínimo, validade, custo). |
| `service_recipes` | **Ficha técnica**: insumo × quantidade por serviço. |
| `stock_movements` | **Ledger de estoque** (entradas, consumos, perdas, ajustes). |

---

## 8. Segurança

- **JWT** HS256, expiração de 8h (480 min).
- **Senha:** PBKDF2-HMAC-SHA256, 200.000 iterações, salt de 16 bytes (sem dependência externa de hash).
- **Dependências de papel:** `get_current_user` (qualquer autenticado) e `require_admin` (admin ou manager).
- **Variáveis sensíveis:** `SECRET_KEY` e `DATABASE_URL` vêm de variáveis de ambiente (arquivo `.env`, com `.env.example` versionado). O servidor **não sobe** se `SECRET_KEY` não estiver definida — sem fallback hardcoded (fail-closed).
- **Rate limiting no login:** `POST /auth/login` bloqueia após 5 tentativas com credenciais erradas em 5 minutos, por (IP, e-mail) → HTTP 429. Só conta tentativas falhas; login certo não consome a cota.
- **Upload de fotos:** o tipo da imagem é identificado pelos **magic bytes** do conteúdo (JPEG/PNG/WebP), não pelo header `Content-Type` enviado pelo cliente (que pode ser falsificado). Limite de 5MB por arquivo.
- **`/uploads/{filename}`:** exige autenticação (qualquer usuário logado) e é sanitizado contra path traversal — deixou de ser servido publicamente como arquivo estático.
- **Concorrência:** `POST /appointments` e `POST /appointments/{id}/complete` rodam sob lock em memória, evitando overbooking e crédito duplicado de pontos de indicação quando duas requisições concorrem.
- **Pendências conhecidas (dev):** rate limiting e locks são por processo único (`threading.Lock`/dict em memória) — corretos para como o projeto roda hoje (`uvicorn` sem `--workers`), mas não coordenariam entre processos num deploy multi-worker; exigiria Redis nesse cenário. Em produção também seria necessário migrar o banco para PostgreSQL (SQLite é single-writer).

---

## 9. Estrutura de arquivos

```
Velour/
├── main.py                  # App FastAPI: CORS, routers, GET /uploads/{filename} (autenticado), /health
├── database.py              # Engine SQLite, sessão, DATABASE_URL via env
├── auth.py                  # JWT + PBKDF2 + dependências de papel (SECRET_KEY obrigatória via env)
├── birthday_scheduler.py    # APScheduler — bônus de aniversário às 08h
├── seed.py                  # Popula o banco com dados de dev
├── requirements.txt         # Dependências de runtime
├── requirements-dev.txt     # Dependências de teste (pytest)
├── .env / .env.example      # Variáveis de ambiente
├── start.bat                # Sobe backend + frontend
│
├── models/                  # ORM SQLAlchemy (user, client, professional, service,
│                            #   appointment, loyalty, referral, product,
│                            #   service_recipe, stock_movement)
├── schemas/                 # Pydantic (request/response)
├── routers/                 # 1 router por domínio (+ products = estoque/ficha técnica)
├── tests/                   # pytest — 58 testes (tiers, loyalty, conflito, indicações,
│                            #   estoque, desconto por tier, painel, alertas,
│                            #   + integração HTTP fim-a-fim: login, 401, 403, 409, rate limit)
│
└── frontend/src/
    ├── api/                 # client.ts (Axios) + types.ts (tipos)
    ├── context/             # AuthContext (JWT)
    ├── components/          # Layout, Sidebar, Modal, TierBadge, StatusBadge, etc.
    └── pages/               # Dashboard, Clients, Appointments, Professionals,
                             #   Services, Inventory, Loyalty, Referrals, Reports, Users
```

---

## 10. Solução de problemas

| Sintoma | Causa | Solução |
|---|---|---|
| Login mostra "Email ou senha incorretos" mesmo com a senha certa | O **backend não está no ar** (o frontend não consegue falar com a API). | Confirme que a janela do backend mostra `Application startup complete`. Use `python -m uvicorn main:app --reload --port 8000`. |
| `Fatal error in launcher: Unable to create process using '...PI.Agendamento...python.exe'` ao rodar `pip`/`uvicorn` | A `.venv` foi copiada de outra pasta; os atalhos `.exe` apontam pro caminho antigo. | Use `python -m pip ...` e `python -m uvicorn ...`. Para resolver de vez: `python -m venv .venv --clear` e reinstalar com `python -m pip install -r requirements.txt`. |
| `npm error ... Could not read package.json` | `npm install` rodado na raiz. | O frontend fica em `frontend/`. Rode `cd frontend; npm install`. |
| Coluna nova não aparece após mudança de modelo | `create_all` não faz `ALTER TABLE`; não há Alembic. | Rode `python seed.py` para recriar o banco (drop + reseed). |
| Backend não sobe: `No module named 'apscheduler'` | Dependências não instaladas no venv. | `python -m pip install -r requirements.txt`. |

---

*Documentação gerada para o projeto Velour. Para detalhes técnicos de implementação, consulte também o `README.md` e o código comentado em português.*
