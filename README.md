# Velour — Backend (FastAPI + SQLite)

API REST do sistema de gestão para salão de beleza premium. Documentação completa (incluindo o frontend) em [`DOCUMENTACAO.md`](DOCUMENTACAO.md).

---

## Como rodar

```bash
# Ativar venv (Windows)
.venv\Scripts\activate

# Primeira execução — popula o banco com dados de desenvolvimento
python seed.py

# Subir o servidor
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Swagger interativo: `http://127.0.0.1:8000/docs`

**Credenciais de dev:**
```
Admin:   admin@velour.com / velour2026
Gerente: gerente@velour.com / velour2026
```

## Testes

```bash
pytest tests/ -v
```

Os testes usam SQLite em memória — não afetam o `velour.db` de desenvolvimento.

---

## Estrutura de arquivos

```
Velour/
├── main.py                  # FastAPI app: CORS, routers, GET /uploads/{filename} (autenticado), /health
├── database.py              # SQLite engine, SessionLocal, get_db()
├── auth.py                  # JWT HS256 + PBKDF2 + get_current_user + require_admin (SECRET_KEY obrigatória via env)
├── birthday_scheduler.py    # APScheduler — 100 pts no aniversário, roda às 08h
├── seed.py                  # Popula banco com dados de dev
│                            # (velour.db é gerado aqui — não commitar)
├── uploads/                 # fotos antes/depois dos atendimentos (servidas via endpoint autenticado)
│
├── models/                  # SQLAlchemy ORM
│   ├── __init__.py          # re-exporta todos os modelos
│   ├── user.py              # User, UserRole
│   ├── client.py            # Client + calculate_tier(), generate_referral_code()
│   ├── professional.py      # Professional, ProfGender
│   ├── service.py           # ServiceCategory, Service, GenderTarget
│   ├── appointment.py       # Appointment, AppointmentStatus
│   ├── loyalty.py           # LoyaltyTransaction, TransactionType
│   ├── referral.py          # Referral, ReferralStatus
│   ├── product.py           # Product, ProductUnit — insumos de estoque
│   ├── service_recipe.py    # ServiceRecipe — ficha técnica (insumo × qtd por serviço)
│   └── stock_movement.py    # StockMovement — ledger append-only de estoque
│
├── schemas/                 # Pydantic — request/response
│   ├── __init__.py
│   ├── user.py
│   ├── client.py
│   ├── professional.py
│   ├── service.py
│   ├── appointment.py
│   ├── loyalty.py
│   ├── referral.py
│   └── product.py           # Product/StockEntry/RecipeItem/RecipeOverride
│
├── routers/                 # Um router por domínio
│   ├── auth.py              # POST /auth/login (rate limited) · GET /auth/me
│   ├── users.py             # /users
│   ├── clients.py           # /clients + /{id}/briefing
│   ├── professionals.py     # /professionals + /{id}/stats
│   ├── services.py          # /service-categories + /services
│   ├── products.py          # /products (estoque) + /services/{id}/recipe (ficha técnica)
│   ├── appointments.py      # /appointments + /{id}/complete + /{id}/photos
│   ├── loyalty.py           # /loyalty/transactions + /loyalty/overview
│   ├── referrals.py         # /referrals + /referrals/ranking
│   ├── dashboard.py         # /dashboard/today|kpis|weekly-revenue|alerts|upcoming
│   └── reports.py           # /reports/revenue|clients|loyalty-monthly|referrals-monthly
│
└── tests/                   # pytest — SQLite em memória (58 testes)
    ├── conftest.py               # fixture db + helpers
    ├── test_tiers.py             # calculate_tier()
    ├── test_loyalty.py           # lógica de desconto e resgate de pontos
    ├── test_tier_discount.py     # desconto automático por tier
    ├── test_appointments.py      # _check_conflict — sobreposição de horário
    ├── test_referrals.py         # conversão de indicação
    ├── test_stock.py             # baixa automática de estoque na conclusão
    ├── test_dashboard_alerts.py  # alertas de estoque baixo/validade
    ├── test_professional_dashboard.py  # meta do mês + cadência de retorno
    └── test_api_integration.py   # HTTP fim-a-fim via TestClient: login, 401, 403, 409, rate limit
```

---

## Modelos de dados

### `users`
| Campo | Tipo | Detalhes |
|---|---|---|
| id | Integer PK | autoincrement |
| name | String(120) | NOT NULL |
| email | String(120) | UNIQUE, indexed |
| hashed_password | String(255) | PBKDF2-HMAC-SHA256, 200k iterações + salt |
| role | Enum | `admin` \| `manager` \| `professional` |
| is_active | Boolean | default True |

### `clients`
| Campo | Tipo | Detalhes |
|---|---|---|
| code | String(20) | `VLR-00001`, gerado automaticamente, UNIQUE |
| name, phone, email | String | email opcional |
| gender | Enum | `M` \| `F` \| `other` |
| birthdate | Date | nullable |
| preferred_drink, music_preference, temperature_preference | String | perfil sensorial |
| chat_preference | Enum | `chatty` \| `quiet` \| `neutral` |
| allergies | String(500) | exibido em destaque no briefing |
| loyalty_points | Integer | default 0 |
| loyalty_tier | Enum | `bronze` \| `silver` \| `gold` \| `platinum` |
| total_spent | Float | acumulado de `price_charged` |
| total_visits | Integer | atendimentos concluídos |
| referral_code | String(20) | 8 chars `[A-Z0-9]`, UNIQUE |
| referred_by_id | FK → clients | nullable |
| is_active | Boolean | soft-delete |

### `professionals`
| Campo | Tipo | Detalhes |
|---|---|---|
| name, phone, email | String | |
| gender | Enum | `M` \| `F` \| `other` |
| specialty | String(300) | ex: "Coloração, Corte Feminino" |
| commission_rate | Float | 0.0–1.0, default 0.40 |
| is_active | Boolean | soft-delete |

### `service_categories`
| Campo | Tipo | Detalhes |
|---|---|---|
| name | String(120) | |
| gender_target | Enum | `M` \| `F` \| `all` |
| icon | String(50) | nome do ícone Lucide (ex: `scissors`) — nullable |

### `services`
| Campo | Tipo | Detalhes |
|---|---|---|
| category_id | FK | NOT NULL |
| duration_minutes | Integer | usado para calcular `ends_at` |
| price | Float | preço-base |
| points_reward | Integer | se > 0, substitui o cálculo de 1pt/R$1 |
| is_active | Boolean | soft-delete |

### `appointments`
| Campo | Tipo | Detalhes |
|---|---|---|
| client_id, professional_id, service_id | FK | |
| scheduled_at | DateTime | horário de início |
| ends_at | DateTime | **calculado no servidor**: `scheduled_at + duration_minutes` |
| status | Enum | `scheduled` → `confirmed` → `in_progress` → `completed` / `cancelled` / `no_show` |
| photo_before_url, photo_after_url | String(500) | upload via `POST /appointments/{id}/photos` |
| formula_used | String(500) | ex: "Wella 6/7 + ox 20vol" |
| points_awarded | Integer | calculado ao concluir |
| price_charged | Float | nullable (relatórios usam `service.price` se NULL) |
| discount_points_used | Integer | default 0 |

### `loyalty_transactions`
| Campo | Tipo | Detalhes |
|---|---|---|
| client_id | FK | |
| appointment_id, referral_id | FK | nullable |
| type | Enum | `earned_appointment` \| `earned_referral` \| `earned_birthday` \| `redeemed` |
| points | Integer | positivo = ganho, negativo = resgate |

### `referrals`
| Campo | Tipo | Detalhes |
|---|---|---|
| referrer_id, referred_id | FK → clients | |
| status | Enum | `pending` → `converted` |
| points_awarded_referrer | Integer | 150 ao converter |
| points_awarded_referred | Integer | 75 ao converter |
| converted_at | DateTime | nullable |
| created_at | DateTime | preenchido automaticamente |

---

## Endpoints

### Autenticação
```
POST /auth/login      body: x-www-form-urlencoded { username, password }
                      response: { access_token, token_type, role, name }
                      token válido por 8 horas

GET  /auth/me         header: Authorization: Bearer <token>
                      response: UserResponse (dados do usuário autenticado)

GET  /health          response: { status: "ok", system: "Velour" }
```

### Usuários — requer admin ou manager
```
GET    /users
POST   /users         body: { name, email, password, role }
PATCH  /users/{id}    body: { name?, role?, is_active? }
```

### Clientes
```
GET    /clients                   query: tier?, gender?, inactive_days?, limit, offset
GET    /clients/{id}
GET    /clients/{id}/briefing     perfil completo + último atendimento + quanto falta pro próximo tier
POST   /clients                   body: ClientCreate
PATCH  /clients/{id}
DELETE /clients/{id}              soft-delete, requer admin
```

### Profissionais
```
GET    /professionals
GET    /professionals/{id}/stats  atendimentos, receita, comissão e ticket médio do mês
POST   /professionals             requer admin
PATCH  /professionals/{id}        requer admin
DELETE /professionals/{id}        soft-delete, requer admin
```

### Serviços
```
GET    /service-categories
POST   /service-categories        body: { name, gender_target, icon? }
PATCH  /service-categories/{id}
DELETE /service-categories/{id}

GET    /services                  query: category_id?, is_active?
POST   /services                  requer admin
PATCH  /services/{id}             requer admin
DELETE /services/{id}             soft-delete, requer admin
```

### Estoque / insumos
```
GET    /products                    query: is_active?, low_stock?
GET    /products/{id}
POST   /products                    requer admin
PATCH  /products/{id}               requer admin — saldo NÃO é editável aqui
DELETE /products/{id}               soft-delete, requer admin
POST   /products/{id}/stock         requer admin — entrada/perda/ajuste, gera movimentação
                                    → rejeita com 422 se a perda deixar o saldo negativo
GET    /products/{id}/movements     histórico do ledger de estoque
```

### Ficha técnica (receita do serviço)
```
GET    /services/{id}/recipe        insumos consumidos pelo serviço
PUT    /services/{id}/recipe        requer admin — substitui a ficha técnica inteira
```

### Agendamentos
```
GET    /appointments              query: date_from?, date_to?, status?, professional_id?, client_id?
GET    /appointments/{id}
POST   /appointments              body: { client_id, professional_id, service_id, scheduled_at, ... }
                                  → calcula ends_at; rejeita com 409 se houver conflito de horário
PATCH  /appointments/{id}/status  body: { status }  — não aceita "completed"
POST   /appointments/{id}/complete body: { price_charged, discount_points_used, formula_used, ... }
                                  → processa pontos, tier e conversão de indicação em uma transação
                                  → discount_points_used deve ser múltiplo de 100
POST   /appointments/{id}/photos  multipart: photo_before?, photo_after?
                                  → identifica o tipo pelos magic bytes do conteúdo (não pelo
                                    Content-Type enviado), salva em uploads/, retorna URLs
DELETE /appointments/{id}         muda status para "cancelled"
```

### Arquivos enviados
```
GET    /uploads/{filename}        requer autenticação (qualquer usuário logado);
                                  sanitizado contra path traversal
```

### Fidelidade
```
GET    /loyalty/transactions      query: client_id?, type?, date_from?, date_to?
GET    /loyalty/overview          total em circulação, emitidos/resgatados no mês, tier dist., top 10
```

### Indicações
```
GET    /referrals                 query: status?, referrer_id?
GET    /referrals/ranking         top 10 indicadores por conversões (todos os tempos)
```

### Dashboard
```
GET    /dashboard/today           agendamentos do dia, receita, breakdown por status
GET    /dashboard/kpis            query: period=day|week|month
GET    /dashboard/weekly-revenue  últimos 7 dias
GET    /dashboard/alerts          aniversariantes do dia + clientes Platinum agendados hoje
GET    /dashboard/upcoming        query: days=2 (1–7)
```

### Relatórios
```
GET    /reports/revenue           query: period_start?, period_end?, professional_id?, category_id?
GET    /reports/clients           query: period_start?, period_end?
GET    /reports/loyalty-monthly   query: months=6
GET    /reports/referrals-monthly query: months=6
```

---

## Regras de negócio

### Pontos de fidelidade

- **Ganho:** `service.points_reward` se > 0; caso contrário `int(price_final) × 1 pt/R$`
- **Resgate:** 100 pts = R$10; múltiplos de 100; teto de 50% do valor do atendimento

```python
# routers/appointments.py
POINTS_PER_BRL = 1
POINTS_REDEMPTION_RATE = 0.10
MAX_DISCOUNT_RATIO = 0.5
REFERRAL_POINTS_REFERRER = 150
REFERRAL_POINTS_REFERRED = 75
```

### Tiers (`models/client.py: calculate_tier`)

| Tier | `total_spent` |
|---|---|
| Bronze | < R$500 |
| Silver | R$500 – R$1.499 |
| Gold | R$1.500 – R$2.999 |
| Platinum | ≥ R$3.000 |

Recalculado em toda conclusão de atendimento. Sem downgrade automático.

### Conflito de horário

Rejeita com HTTP 409 se para o mesmo profissional:
```
existing.scheduled_at < new.ends_at
AND existing.ends_at > new.scheduled_at
AND existing.status NOT IN ('cancelled', 'no_show')
```

### Conversão de indicação

Disparada no primeiro atendimento concluído de um cliente indicado:
1. Localiza `Referral(referred_id=cliente, status=pending)`
2. `status → converted`, `converted_at = now()`
3. +150 pts ao referrer, +75 pts ao referred
4. Cria 2 `LoyaltyTransaction(type=earned_referral)`

### Bônus de aniversário

`birthday_scheduler.py` roda às 08h00 via APScheduler:
- Busca clientes ativos com `birthdate` no dia de hoje
- Adiciona 100 pts + `LoyaltyTransaction(type=earned_birthday)`
- Idempotente: não concede se já existe `earned_birthday` no mês atual

### Segurança

```
JWT: HS256, 480 min de expiração
Senha: PBKDF2-HMAC-SHA256, 200.000 iterações, salt de 16 bytes

Roles:
  get_current_user()  → qualquer usuário autenticado
  require_admin()     → admin ou manager
```

- `SECRET_KEY` e `DATABASE_URL` vêm de variáveis de ambiente (`.env`, com `.env.example` versionado). O servidor **recusa subir** se `SECRET_KEY` não estiver definida — sem fallback hardcoded.
- Upload de fotos identifica o tipo da imagem pelos **magic bytes** do conteúdo (JPEG/PNG/WebP), não pelo header `Content-Type` enviado pelo cliente — evita que um arquivo com extensão/tipo falsificado seja aceito. Limite de 5MB por arquivo.
- `/uploads/{filename}` exige autenticação e é sanitizado contra path traversal.
- `POST /auth/login` tem rate limiting em memória: 5 tentativas com credenciais erradas em 5 minutos por (IP, e-mail) → HTTP 429. Logins bem-sucedidos não consomem a cota.
- `POST /appointments` e `POST /appointments/{id}/complete` rodam sob lock (processo único): evita overbooking sob requisições concorrentes e evita que a conclusão simultânea de dois atendimentos credite pontos de indicação em duplicidade.

> **Pendência conhecida:** rate limiting e locks funcionam por processo único (`threading.Lock`, dict em memória) — suficiente para como o projeto roda (`uvicorn` sem `--workers`), mas não seria em um deploy multi-worker/multi-processo. Em produção, precisaria de Redis para coordenar entre processos.

---

## Dados de dev (`seed.py`)

| Entidade | Qt. | Detalhes |
|---|---|---|
| Users | 2 | admin + gerente |
| Professionals | 4 | Ana Luiza (coloração/cabelo F), Beatriz (unhas), Carlos (barbearia), Diego (barbearia + coloração M) |
| Service Categories | 5 | Cabelo F, Coloração, Barbearia, Manicure & Pedicure, Cabelo M |
| Services | 15 | R$80–R$550, 30–180 min |
| Clients | 20 | 10F + 10M, tiers variados, perfil sensorial preenchido |
| Appointments | 30 | mix passados/futuros, status realistas, sem conflitos, serviços compatíveis com especialidade |
| Referrals | 8 | 5 convertidas (created_at retroativo) + 3 pendentes |
| Loyalty Transactions | ~20 | 1 por atendimento concluído + bônus de aniversário |
