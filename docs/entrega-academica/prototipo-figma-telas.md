# Especificação para o protótipo no Figma

O protótipo existe no Figma Make: https://www.figma.com/make/b2WZxFKGy7MKOfKsXn8fFk/Execute-task. O arquivo é privado, da conta do autor. Foi lido pelo Opera em 29/09/2026. Só a tela de login foi vista de fato. O restante vem do resumo que o próprio Figma Make gerou no chat do projeto.

Este documento continua útil como especificação do que ainda falta ao protótipo. A lista foi tirada das rotas e dos componentes reais do frontend.

## Protótipo existente versus sistema

O protótipo tem 10 telas navegáveis, segundo o resumo do Figma Make: Login com validação, Dashboard, Clientes, Agendamentos com detecção de conflito no formulário, Profissionais com comissão, Serviços com categorias, Fidelidade, Indicações, Relatórios com quatro abas de gráficos e Usuários com os três perfis.

O sistema tem 16 telas. Não constam no protótipo:

- Perfil do cliente, em `/clients/:id`.
- Estoque.
- Financeiro, com Visão geral, Recebimentos, Despesas, Contábil, Documentos fiscais e Assinatura.
- Cadastro do salão e recuperação de senha.
- Administração Velour.

A identidade visual difere um pouco. O protótipo usa fundo `#0D0C0B`, ouro `#BF9B5F` e as fontes DM Serif Display, Outfit e DM Mono, com o subtítulo "Studio Management". O sistema usa `#0A0A0A`, `#C9A84C`, Cormorant Garamond, DM Sans e JetBrains Mono, com "Gestão Premium". Na tela de login vista, o botão aparece em âmbar mais vivo que o ouro descrito. Como a professora cobra alinhamento entre Figma e código, convém igualar as cores e as fontes, ou explicar que o protótipo veio antes.

## Referência visual

A pasta [telas](telas) tem capturas de 1440 por 900 pixels das 16 telas do administrador, tiradas em 29/09/2026 com dados fictícios do `seed.py`. Use-as como referência para reproduzir o layout no Figma. Elas mostram o estado carregado. Os estados de carregamento, vazio e erro precisam ser desenhados à parte.

## Organização do arquivo

Crie um arquivo chamado Velour com quatro páginas: **Fundamentos**, **Componentes**, **Telas** e **Fluxos**. Desenhe em 1440 px de largura e repita as telas principais em 390 px, largura já usada na verificação responsiva do projeto.

## Fundamentos

Os valores vêm de `frontend/src/index.css`.

| Item | Valor |
|---|---|
| Fundo | `#0A0A0A` |
| Superfície | `#111111` |
| Borda | `#1E1E1E` |
| Dourado | `#C9A84C`, versão apagada `#8A6F2E` |
| Creme, texto | `#F5F4F0` |
| Texto secundário | `#969696` |
| Sucesso | `#4A7C59` |
| Erro | `#8B2635` |
| Fonte de destaque | Cormorant Garamond |
| Fonte de texto | DM Sans |
| Fonte monoespaçada | JetBrains Mono |

## Componentes

Componentes existentes em `frontend/src/components`, cada um com seus estados:

- **Sidebar e Layout:** menu lateral. Para o profissional, o código oculta apenas Relatórios e a seção Administração, que tem Usuários. Estoque, Fidelidade, Indicações e Financeiro continuam no menu, e a API nega o acesso a elas. Decida se o protótipo segue o código atual ou esconde esses itens.
- **Modal:** aberto, com erro de validação e com envio em andamento.
- **StatusBadge:** `scheduled`, `confirmed`, `in_progress`, `completed`, `cancelled`, `no_show`.
- **TierBadge:** Bronze, Silver, Gold, Platinum.
- **BriefingDrawer:** preferências, alergias, observações e último atendimento.
- **Spinner, LoadError e ErrorBoundary:** carregamento, falha com nova tentativa e erro inesperado.
- **PrivatePhoto:** foto carregando, exibida e sem permissão.

## Telas

Desenhe cada tela com os estados de carregamento, vazio e erro. Papéis: A é administrador, G é gerente, P é profissional.

| Rota | Tela | Papéis | Conteúdo principal |
|---|---|---|---|
| `/login` | Login | Público | E-mail, senha, link para recuperação. |
| `/signup` | Cadastro do salão | Público | Nome do salão, administrador, e-mail, senha e aceite dos termos. |
| `/forgot-password` e `/reset-password` | Recuperação de senha | Público | Pedido de link e definição de nova senha. |
| `/` | Dashboard | A, G, P | Agenda de hoje, receita, KPIs, próximos atendimentos, aniversariantes, Platinum e alertas de estoque. |
| `/clients` | Clientes | A, G, P | Lista paginada com filtros por nível, gênero e inatividade. |
| `/clients/:id` | Perfil do cliente | A, G, P | Preferências, fidelidade, histórico e indicações. |
| `/appointments` | Agendamentos | A, G, P | Lista com filtros, criação, mudança de status, conclusão e fotos. |
| `/professionals` | Profissionais | A, G, P | Cadastro, comissão, meta e clientes a recuperar. |
| `/services` | Serviços | A, G, P | Catálogo, categorias e ficha técnica. |
| `/inventory` | Estoque | A, G | Insumos, entradas, perdas, validade e movimentações. |
| `/loyalty` | Fidelidade | A, G | Pontos, distribuição de níveis e transações. |
| `/referrals` | Indicações | A, G | Pendentes, convertidas e ranking. |
| `/reports` | Relatórios | A, G | Receita, clientes, fidelidade e indicações por período. |
| `/users` | Usuários | A, G | Cadastro, papel, vínculo profissional e ativação. |
| `/billing` | Conta e assinatura | Todos veem, A gerencia | Situação, Checkout, Portal e exportação. |
| `/finance/overview` | Financeiro, visão geral | A, G | Resumo mensal. |
| `/finance/documents` | Documentos fiscais | A | Cadastro, rascunho, emissão simulada e cancelamento. |
| `/finance/accounting` | Contábil | A, G | DRE, livro diário e balancete, com download em TXT e PDF. |

O Financeiro também tem as abas Recebimentos, Despesas e Assinatura Velour, sob `/finance/:section`. Desenhe uma variação de cada. O modal de conclusão do atendimento merece um quadro próprio, com valor base, resgate de pontos, desconto do nível, teto de 50%, pagamento e consumo de estoque.

## Fluxos para o protótipo clicável

1. **Primeiro acesso:** cadastro, chegada em `/billing?welcome=1`, cadastro de serviço, profissional e cliente.
2. **Atendimento:** criar agendamento, confirmar, concluir com resgate de pontos e ver os pontos no perfil do cliente.
3. **Conflito de agenda:** tentar horário ocupado e ver a mensagem de conflito.
4. **Assinatura vencida:** qualquer rota de negócio leva a `/billing`.
5. **Profissional:** login e lista só com os próprios atendimentos.
