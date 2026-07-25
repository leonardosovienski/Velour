# Velour — Frontend React

SPA do sistema de gestão para salão de beleza premium. Documentação do backend em [`../README.md`](../README.md).

---

## Como rodar

```bash
npm install   # primeira vez
npm run dev   # http://localhost:5173
```

Para build de produção:
```bash
npm run build   # gera dist/
npm run preview # pré-visualiza o build
```

Requer o backend rodando em `http://127.0.0.1:8000` (ver `../README.md`).

> **Atenção:** a URL base do backend está hardcoded em `api/client.ts`.
> Para outros ambientes, extraia para uma variável `VITE_API_URL`.

---

## Stack

| Pacote | Versão | Uso |
|---|---|---|
| React | 19 | UI |
| TypeScript | 5.x | Tipagem estática |
| Vite | 6.x | Bundler + dev server |
| Tailwind CSS | 3.x | Estilos utilitários |
| Axios | — | HTTP client |
| React Router | v6 | Roteamento client-side |
| Lucide React | — | Ícones |
| date-fns | — | Formatação de datas |

---

## Estrutura de arquivos

```
frontend/src/
├── main.tsx                  # Monta React na div#root
├── App.tsx                   # BrowserRouter + AuthProvider + rotas protegidas
│
├── api/
│   ├── types.ts              # Todos os tipos TypeScript (espelham schemas Pydantic)
│   └── client.ts             # Funções de API agrupadas por domínio (axios)
│
├── context/
│   └── AuthContext.tsx       # AuthProvider + useAuth — token em localStorage
│
├── components/
│   ├── Layout.tsx            # Shell com Sidebar + <Outlet>
│   ├── Sidebar.tsx           # Navegação lateral; adminItems visível só p/ admin/manager
│   ├── Modal.tsx             # Modal genérico (backdrop + Escape)
│   ├── Spinner.tsx           # SVG animado dourado
│   ├── TierBadge.tsx         # Badge colorido por tier (bronze/silver/gold/platinum)
│   ├── StatusBadge.tsx       # Badge por status de atendimento
│   └── BriefingDrawer.tsx    # Painel lateral deslizante com briefing completo do cliente
│
└── pages/
    ├── Login.tsx             # Tela de login com JWT
    ├── Dashboard.tsx         # Visão geral do dia + KPIs + alertas
    ├── Clients.tsx           # Lista, busca, filtro por tier/gênero, criação e edição
    ├── ClientProfile.tsx     # Perfil detalhado + histórico + indicações
    ├── Appointments.tsx      # Agenda, criação, mudança de status e conclusão
    ├── Professionals.tsx     # Lista de profissionais + stats do mês
    ├── Services.tsx          # Categorias com ícone Lucide + serviços
    ├── Loyalty.tsx           # Transações de pontos + overview
    ├── Referrals.tsx         # Lista de indicações + ranking dos melhores indicadores
    ├── Reports.tsx           # Abas: Receita, Clientes, Fidelidade, Indicações
    └── Users.tsx             # Gestão de usuários do sistema (admin/manager)
```

---

## Autenticação

`AuthContext` armazena o token JWT no `localStorage` (`access_token`, `user_name`, `user_role`). Todas as requisições Axios incluem o header `Authorization: Bearer <token>` via interceptor em `api/client.ts`.

Rotas são protegidas por `ProtectedRoute` — redireciona para `/login` se não autenticado. `PublicRoute` redireciona para `/` se já autenticado.

---

## Páginas

### Login (`/login`)
Formulário de e-mail + senha. Chama `POST /auth/login` e armazena o token.

### Dashboard (`/`)
- Card com atendimentos do dia, receita e breakdown por status
- KPIs configuráveis (dia / semana / mês): atendimentos concluídos, receita, novos clientes, pontos emitidos
- Gráfico de barras com receita dos últimos 7 dias
- Painel de alertas: aniversariantes do dia e clientes Platinum agendados

### Clientes (`/clients`)
- Tabela paginada com busca por nome/código, filtro por tier e gênero
- Criação via modal com todos os campos do perfil sensorial
- Edição inline por modal
- Soft-delete (requer admin)
- Link para o perfil individual

### Perfil do Cliente (`/clients/:id`)
- Cabeçalho com tier badge, pontos, total gasto, total de visitas
- Botão para abrir `BriefingDrawer` — painel lateral com preferências, alergias, última fórmula usada
- Histórico de atendimentos com status e valor
- Lista de indicações feitas pelo cliente

### Agendamentos (`/appointments`)
- Tabela com filtros de data, status e profissional
- Criação via modal: seleciona cliente, profissional, serviço e horário
- Mudança de status via dropdown (exceto "concluído")
- Modal de conclusão: valor cobrado, desconto em pontos (múltiplos de 100), fórmula usada e upload de fotos (antes/depois)

### Profissionais (`/professionals`)
- Lista de profissionais ativos com especialidade e taxa de comissão
- Card de stats do mês: atendimentos, receita, comissão e ticket médio
- Criação e edição por modal (requer admin)

### Serviços (`/services`)
- Categorias exibidas com ícone Lucide mapeado pelo campo `icon` (ex: `scissors` → `<Scissors>`)
- Serviços agrupados por categoria com duração, preço e pontos de recompensa
- Criação e edição de categorias e serviços (requer admin)

### Fidelidade (`/loyalty`)
- Extrato de transações com filtros por cliente, tipo e data
- Overview: total em circulação, emitidos/resgatados no mês, distribuição por tier, top 10 clientes

### Indicações (`/referrals`)
- Lista de indicações com status (pendente / convertida)
- Ranking dos 10 melhores indicadores por conversões

### Relatórios (`/reports`)
Quatro abas com período configurável:
- **Receita:** total, por profissional, por categoria e por gênero
- **Clientes:** novos, em risco de churn, distribuição por tier
- **Fidelidade:** pontos emitidos vs resgatados por mês (últimos N meses)
- **Indicações:** indicações criadas, convertidas, taxa de conversão e pontos investidos por mês

### Usuários (`/users`) — admin e manager
- Lista de usuários do sistema com role e status
- Toggle de ativo/inativo
- Edição de nome e role por modal
- Criação de novo usuário (nome, e-mail, senha, role)

---

## Identidade visual

| Token | Valor |
|---|---|
| `bg` (fundo) | `#0A0A0A` |
| `surface` (cards) | `#141414` |
| `gold` (destaque) | `#C9A84C` |
| `cream` (texto principal) | `#F5F0E8` |
| `muted` (texto secundário) | `#6B6B6B` |
| `border` | `rgba(255,255,255,0.08)` |

**Fontes:**
- `Cormorant Garamond` — títulos e logo (`font-display`)
- `DM Sans` — corpo de texto
- `JetBrains Mono` — dados numéricos e códigos

---

## Tipos e API

`api/types.ts` exporta todos os tipos TypeScript que espelham os schemas Pydantic do backend. Os valores dos enums devem ser exatamente os retornados pela API:

| Tipo | Valores |
|---|---|
| `Gender` | `'M'` \| `'F'` \| `'other'` |
| `ChatPreference` | `'chatty'` \| `'quiet'` \| `'neutral'` |
| `AppointmentStatus` | `'scheduled'` \| `'confirmed'` \| `'in_progress'` \| `'completed'` \| `'cancelled'` \| `'no_show'` |
| `LoyaltyTxType` | `'earned_appointment'` \| `'earned_referral'` \| `'earned_birthday'` \| `'redeemed'` |
| `gender_target` | `'M'` \| `'F'` \| `'all'` |

`api/client.ts` agrupa as funções de API por domínio:

```ts
authApi          // login, /me
usersApi         // CRUD usuários
clientsApi       // CRUD clientes + briefing
professionalsApi // CRUD profissionais + stats
servicesApi      // categorias + serviços
appointmentsApi  // CRUD + complete + uploadPhotos
loyaltyApi       // transactions + overview
referralsApi     // lista + ranking
dashboardApi     // today, kpis, weekly-revenue, alerts, upcoming
reportsApi       // revenue, clients, loyalty-monthly, referrals-monthly
```
