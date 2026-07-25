# VELOUR — Sistema de Gestão para Salão Premium
## Prompt para Claude Code

---

## VISÃO DO PRODUTO

Construa **Velour**, um sistema de gestão interno para salões de beleza de alto padrão, atendendo homens e mulheres. O sistema é usado exclusivamente pelos profissionais e gestores do salão — não há acesso do cliente final. O diferencial é a experiência: o profissional abre o agendamento do dia e já sabe tudo sobre o cliente antes de ele sentar na cadeira.

O posicionamento é **luxo funcional** — cada detalhe da interface deve transmitir sofisticação. Não é um sistema genérico de agendamento. É uma ferramenta que um salão caro colocaria na mão de seus profissionais.

---

## TECH STACK

```
Backend:  FastAPI (Python 3.11+)
ORM:      SQLAlchemy + Alembic (migrations)
Database: SQLite (desenvolvimento) → facilmente migrável para PostgreSQL
Auth:     JWT (python-jose) + bcrypt
Frontend: React 18 + Vite + TypeScript
Styling:  Tailwind CSS + CSS custom properties
Icons:    Lucide React
HTTP:     Axios com interceptors para JWT
State:    React Context + useReducer (sem Redux)
```

---

## IDENTIDADE VISUAL

**Nome:** Velour  
**Conceito:** Minimalismo luxuoso. Preto profundo, dourado discreto, branco sujo. Tipografia elegante. Sem elementos desnecessários.

```css
--color-bg:        #0A0A0A;   /* preto profundo */
--color-surface:   #111111;   /* superfície de cards */
--color-border:    #1E1E1E;   /* bordas sutis */
--color-gold:      #C9A84C;   /* dourado — accent principal */
--color-gold-dim:  #8A6F2E;   /* dourado escuro */
--color-white:     #F5F4F0;   /* branco sujo */
--color-gray:      #6B6B6B;   /* texto secundário */
--color-success:   #4A7C59;   /* verde escuro */
--color-danger:    #8B2635;   /* vermelho escuro */

--font-display:    'Cormorant Garamond', serif;   /* títulos — elegante */
--font-body:       'DM Sans', sans-serif;         /* corpo — limpo */
--font-mono:       'JetBrains Mono', monospace;   /* dados, números */
```

Carregar via Google Fonts. Sidebar escura. Cards com borda sutil. Botões de ação com dourado. Tabelas sem excesso de linhas. Muita respiração entre elementos.

---

## ESTRUTURA DE ARQUIVOS

```
velour/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── auth.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── client.py
│   │   ├── professional.py
│   │   ├── service.py
│   │   ├── appointment.py
│   │   ├── loyalty.py
│   │   └── referral.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── clients.py
│   │   ├── professionals.py
│   │   ├── services.py
│   │   ├── appointments.py
│   │   ├── loyalty.py
│   │   ├── referrals.py
│   │   ├── dashboard.py
│   │   └── reports.py
│   ├── schemas/
│   │   └── (Pydantic schemas espelhando os models)
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/
    │   │   └── client.ts
    │   ├── context/
    │   │   └── AuthContext.tsx
    │   ├── components/
    │   │   ├── ui/           (Button, Input, Badge, Modal, etc.)
    │   │   ├── layout/       (Sidebar, Header, PageWrapper)
    │   │   └── shared/       (ClientCard, AppointmentCard, TierBadge)
    │   └── pages/
    │       ├── Login.tsx
    │       ├── Dashboard.tsx
    │       ├── Clients/
    │       ├── Professionals/
    │       ├── Services/
    │       ├── Appointments/
    │       ├── Loyalty/
    │       ├── Referrals/
    │       └── Reports/
    ├── index.html
    ├── vite.config.ts
    ├── tailwind.config.ts
    └── package.json
```

---

## DATABASE — MODELOS COMPLETOS

### User (gestores e profissionais do sistema)
```python
id: int (PK)
name: str
email: str (unique)
hashed_password: str
role: enum ['admin', 'manager', 'professional']
is_active: bool
created_at: datetime
```

### Client
```python
id: int (PK)
code: str (unique, ex: "VLR-00042")     # código único do cliente
name: str
phone: str
email: str (nullable)
gender: enum ['M', 'F', 'other']
birthdate: date (nullable)
first_visit: date                        # data da primeira visita
photo_url: str (nullable)

# Perfil sensorial (experiência premium)
preferred_drink: str (nullable)          # café, espumante, chá, água
music_preference: str (nullable)         # jazz, pop, silêncio
temperature_preference: str (nullable)   # fria, agradável, quente
chat_preference: enum ['chatty', 'quiet', 'neutral'] (default 'neutral')
allergies: str (nullable)                # alergias a produtos
notes: str (nullable)                    # observações gerais

# Fidelidade
loyalty_points: int (default 0)
loyalty_tier: enum ['bronze', 'silver', 'gold', 'platinum'] (default 'bronze')
total_spent: float (default 0.0)
total_visits: int (default 0)

# Indicação
referral_code: str (unique)              # código único de indicação
referred_by_id: int (FK → Client, nullable)

is_active: bool (default True)
created_at: datetime
```

### Professional
```python
id: int (PK)
name: str
phone: str
email: str (nullable)
gender: enum ['M', 'F', 'other']
photo_url: str (nullable)
specialty: str                           # ex: "Coloração, Corte feminino"
bio: str (nullable)
commission_rate: float (default 0.40)    # 40% de comissão
is_active: bool
created_at: datetime
```

### ServiceCategory
```python
id: int (PK)
name: str                                # ex: "Cabelo Feminino", "Barba", "Estética"
gender_target: enum ['M', 'F', 'all']
icon: str (nullable)
```

### Service
```python
id: int (PK)
category_id: int (FK → ServiceCategory)
name: str
description: str (nullable)
duration_minutes: int
price: float
points_reward: int                       # pontos que o cliente ganha ao realizar este serviço
is_active: bool
created_at: datetime
```

### Appointment
```python
id: int (PK)
client_id: int (FK → Client)
professional_id: int (FK → Professional)
service_id: int (FK → Service)
scheduled_at: datetime
ends_at: datetime                        # calculado automaticamente (scheduled_at + duration)
status: enum ['scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show']
occasion: str (nullable)                 # casamento, aniversário, formatura, evento
notes: str (nullable)                    # observações do agendamento
photo_before_url: str (nullable)
photo_after_url: str (nullable)
formula_used: str (nullable)             # para coloração: fórmula aplicada
points_awarded: int (default 0)
price_charged: float (nullable)          # preço final (pode ter desconto)
discount_points_used: int (default 0)
created_at: datetime
```

### LoyaltyTransaction
```python
id: int (PK)
client_id: int (FK → Client)
appointment_id: int (FK → Appointment, nullable)
referral_id: int (FK → Referral, nullable)
type: enum ['earned_appointment', 'earned_referral', 'earned_birthday', 'redeemed']
points: int                              # positivo = ganhou, negativo = usou
description: str
created_at: datetime
```

### Referral
```python
id: int (PK)
referrer_id: int (FK → Client)          # quem indicou
referred_id: int (FK → Client)          # quem foi indicado
status: enum ['pending', 'converted']   # converted = indicado fez primeiro agendamento
points_awarded_referrer: int (default 0)
points_awarded_referred: int (default 0)
converted_at: datetime (nullable)
created_at: datetime
```

---

## REGRAS DE NEGÓCIO — FIDELIDADE

### Acúmulo de pontos
```
Atendimento realizado:     1 ponto por R$1 gasto (arredondado)
Indicação convertida:      referrer ganha 150 pontos + referred ganha 75 pontos
                           (conversão = indicado completa primeiro atendimento)
Aniversário do cliente:    100 pontos automáticos no mês do aniversário
Aniversário de 1 ano
como cliente Velour:       50 pontos automáticos
```

### Tiers (baseado em total_spent acumulado)
```
Bronze:   R$ 0 a R$ 499        → sem benefício extra
Silver:   R$ 500 a R$ 1.499    → 5% desconto em serviços + pontos em dobro no aniversário
Gold:     R$ 1.500 a R$ 2.999  → 10% desconto + acesso a horários preferenciais
Platinum: R$ 3.000+            → 15% desconto + serviço cortesia a cada 500 pontos + atendimento prioritário
```

### Resgate de pontos
```
100 pontos = R$ 10 de desconto
Mínimo de resgate: 100 pontos
Máximo de desconto por atendimento: 50% do valor do serviço
```

### Recálculo automático de tier
Sempre que um atendimento é marcado como `completed`:
1. Somar valor ao `total_spent` do cliente
2. Calcular `loyalty_points` ganhos
3. Recalcular `loyalty_tier` com base no novo `total_spent`
4. Registrar `LoyaltyTransaction`
5. Verificar se indicação pendente deve ser convertida

---

## PÁGINAS E FUNCIONALIDADES

### 1. Login
- Campos: usuário (email) e senha
- JWT armazenado em httpOnly cookie ou localStorage
- Redireciona para Dashboard após autenticação
- Estética: tela dividida, lado esquerdo com identidade Velour (nome, tagline), lado direito com formulário minimalista

### 2. Dashboard
KPIs no topo:
- Atendimentos do dia (com status breakdown)
- Receita do dia / semana / mês (toggle)
- Clientes ativos
- Pontos emitidos no mês

Seções:
- **Agenda de hoje** — lista de atendimentos com horário, cliente (com tier badge), profissional, serviço, status. Ao clicar no agendamento, abre briefing completo do cliente
- **Próximos atendimentos** — amanhã e depois
- **Alertas** — aniversários do dia, indicações convertidas, clientes Platinum agendados
- **Performance semanal** — mini gráfico de barras por dia

### 3. Clientes
Lista com:
- Código VLR, avatar (iniciais), nome, tier badge, telefone, total de visitas, total gasto, pontos atuais
- Filtros: tier, gênero, profissional preferido, sem agendamento há mais de 60 dias

**Perfil do cliente** (página dedicada):
Abas:
- **Visão Geral** — dados pessoais, perfil sensorial (bebida, música, temperatura, preferência de conversa), alergias, observações
- **Histórico** — todos os atendimentos com data, profissional, serviço, valor, fórmula usada, fotos antes/depois
- **Fidelidade** — pontos totais, tier atual, barra de progresso para o próximo tier, histórico de transações de pontos
- **Indicações** — código único do cliente, quantas indicações fez, quantas converteram, pontos ganhos por indicação

**Cadastro/Edição de cliente:**
Todos os campos incluindo perfil sensorial. Campo de código de indicação (quem o indicou).

### 4. Profissionais
Lista com: foto, nome, especialidade, comissão configurada, total de atendimentos do mês, receita gerada

**Perfil do profissional:**
- Dados pessoais e especialidade
- Agenda da semana
- KPIs: ticket médio, serviços mais realizados, taxa de retorno de clientes, comissão do mês

### 5. Serviços
Organizado por categoria (com ícone e gênero-alvo):
- Categorias: Cabelo Feminino, Cabelo Masculino, Barba & Barbearia, Coloração, Manicure & Pedicure, Estética, Sobrancelha & Cílios, Depilação, Massagem

Cada serviço: nome, categoria, duração, preço, pontos que concede ao cliente

### 6. Agendamentos
**Criar agendamento:**
- Select de cliente (busca por nome ou código VLR)
- Select de profissional (filtrado por especialidade compatível com o serviço)
- Select de serviço (filtrado por profissional selecionado)
- Data e horário (com verificação de conflito)
- Campo de ocasião (nullable)
- Campo de observações

**Lista de agendamentos:**
- Filtros: data, status, profissional, cliente
- Badge de tier do cliente visível na listagem
- Ações: confirmar, iniciar, concluir (abre modal de conclusão), cancelar, marcar no-show

**Modal de conclusão:**
- Confirmar valor cobrado
- Campo para usar pontos de desconto (mostra saldo disponível)
- Upload de foto antes/depois
- Campo de fórmula usada (aparece se serviço for de coloração)
- Resumo automático: valor original, desconto por pontos, valor final, pontos que o cliente vai ganhar

### 7. Fidelidade
**Visão geral:**
- Total de pontos em circulação
- Distribuição de clientes por tier (donut chart)
- Top 10 clientes por pontos
- Pontos emitidos vs resgatados no mês

**Histórico de transações:**
- Filtro por cliente, tipo (ganhou/resgatou), período

### 8. Indicações
- Tabela: quem indicou → quem foi indicado → status (pendente/convertida) → pontos concedidos → data
- Card de ranking: top indicadores do mês
- Filtro por status e período

### 9. Relatórios
- **Receita:** por período, por profissional, por categoria de serviço, por gênero do cliente
- **Clientes:** novos por mês, taxa de retorno, churn (não voltou há 60+ dias)
- **Fidelidade:** pontos emitidos/resgatados por mês, distribuição por tier
- **Indicações:** conversões por mês, ROI em pontos investidos
- Todos os relatórios com gráfico + tabela exportável

---

## BRIEFING PRÉ-ATENDIMENTO (componente especial)

Quando o profissional clica em um agendamento no Dashboard, abre um painel lateral (drawer) com:

```
┌─────────────────────────────────────┐
│  ◆ GOLD  Maria Fernandes            │
│  VLR-00042  •  Cliente há 2 anos    │
├─────────────────────────────────────┤
│  OCASIÃO                            │
│  🎂 Aniversário de 40 anos          │
├─────────────────────────────────────┤
│  PREFERÊNCIAS                       │
│  ☕ Café sem açúcar                 │
│  🎵 Jazz instrumental               │
│  🌡 Temperatura agradável           │
│  💬 Prefere não conversar           │
├─────────────────────────────────────┤
│  ÚLTIMO ATENDIMENTO (12/04/2026)    │
│  Coloração — Ana Luiza              │
│  Fórmula: Wella 7.3 + 7.0 (50/50)  │
│  "Quer aprofundar o dourado"        │
├─────────────────────────────────────┤
│  ALERGIAS                           │
│  Amônia concentrada                 │
├─────────────────────────────────────┤
│  FIDELIDADE                         │
│  ★ 1.240 pontos  •  Gold            │
│  Faltam R$300 para Platinum         │
└─────────────────────────────────────┘
```

---

## SEED DATA (para desenvolvimento)

Criar script `seed.py` que popula:
- 1 admin (admin@velour.com / velour2026)
- 4 profissionais (2 feminino, 2 masculino)
- 15 serviços em 5 categorias
- 20 clientes com perfis variados (tiers variados, histórico de indicações)
- 30 agendamentos (passados e futuros, status variados)
- Transações de fidelidade consistentes com o histórico

---

## REGRAS DE IMPLEMENTAÇÃO

1. **API primeiro** — implementar e testar todos os endpoints antes de iniciar o frontend
2. **Validações no backend** — nunca confiar apenas no frontend para regras de negócio
3. **Recálculo de tier sempre no backend** — endpoint `POST /appointments/{id}/complete` deve triggar o recálculo
4. **Conflito de horários** — endpoint de criação de agendamento deve verificar se profissional já tem agendamento no mesmo horário (considerando duração do serviço)
5. **Código VLR** — gerado automaticamente no cadastro: `VLR-` + número sequencial com 5 dígitos (VLR-00001)
6. **Código de indicação** — 8 caracteres alfanuméricos únicos gerado no cadastro do cliente
7. **CORS** configurado para `localhost:5173` (Vite dev server)
8. **Swagger** disponível em `/docs`
9. **Sem paginação simplificada** — usar limit/offset com total_count no header ou body
10. **Datas sempre em UTC** — frontend converte para exibição

---

## ORDEM DE IMPLEMENTAÇÃO SUGERIDA

```
Fase 1 — Backend core
  1. Setup FastAPI + SQLAlchemy + Alembic
  2. Models + migrations
  3. Auth (JWT)
  4. CRUD: clients, professionals, services, appointments
  5. Lógica de fidelidade (complete appointment → points → tier)
  6. Lógica de indicação (referral conversion)
  7. Dashboard aggregations
  8. Reports aggregations
  9. Seed script
  10. Testar todos os endpoints no Swagger

Fase 2 — Frontend
  1. Setup Vite + React + TypeScript + Tailwind
  2. Configurar fontes (Cormorant Garamond + DM Sans)
  3. Design system: tokens CSS, componentes base (Button, Input, Badge, Modal)
  4. Layout: Sidebar + Header
  5. Login page
  6. Dashboard + Briefing drawer
  7. Clientes (lista + perfil completo)
  8. Agendamentos (lista + criar + modal de conclusão)
  9. Profissionais
  10. Serviços + Categorias
  11. Fidelidade
  12. Indicações
  13. Relatórios

Fase 3 — Refinamento
  1. Responsividade mobile
  2. Loading states e error handling
  3. Toasts de feedback
  4. Animações de transição de página
  5. Empty states com ilustração
```

---

## COMANDOS PARA INICIAR

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn sqlalchemy alembic python-jose[cryptography] bcrypt pydantic python-multipart
alembic init alembic
# configurar alembic.ini e env.py
alembic revision --autogenerate -m "initial"
alembic upgrade head
python seed.py
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm create vite@latest . -- --template react-ts
npm install axios lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm run dev
```

---

## IMPORTANTE

- Não usar CSS genérico. A interface precisa transmitir luxo. Fundos escuros, dourado como accent, tipografia com serifa nos títulos.
- Cada página deve ter um empty state bem desenhado (não só "sem dados").
- O briefing pré-atendimento é o feature mais importante — priorizá-lo visualmente.
- Comentar o código em português.
- Nomes de variáveis e funções em inglês (padrão técnico).
- Toda lógica de pontos e tier deve ter testes unitários (`pytest`).
