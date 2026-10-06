# Guia da disciplina e situação do Velour

Transcrição do "Guia do Aluno & Plano de Execução — Projeto Integrador VI / Multidisciplinar VI (2026/2)", a partir das fotos das páginas recebidas em 06/10/2026, com a situação do Velour em cada exigência nessa data. É o material que o [README](README.md) desta pasta registrava como "não lido".

## O que o guia exige

O grupo atua como consultoria de TI. O produto é uma aplicação de porte corporativo, com foco em módulos como **Financeiro, Contabilidade e Gestão de Custos**, construída em código funcional, com front-end, back-end e banco de dados. A gestão segue o método ágil, com Jira, Confluence e Figma, e o código fica versionado e rastreável no GitHub.

| Exigência | No Velour | Onde ver |
|---|---|---|
| Módulo Financeiro | Recebimentos, despesas e resumo do mês | [FINANCEIRO_MVP.md](../../FINANCEIRO_MVP.md), `routers/finance.py`, `pages/Finance.tsx` |
| Módulo de Contabilidade | DRE, livro diário, balancete e download em TXT ou PDF, todos demonstrativos | `routers/accounting.py`, `pages/Accounting.tsx` |
| Módulo de Gestão de Custos | **Novo em 06/10/2026.** Margem de contribuição, ponto de equilíbrio, orçado × realizado, margem por serviço e por profissional, custo-padrão da ficha técnica, evolução de seis meses, alertas e CSV | [FINANCEIRO_MVP.md](../../FINANCEIRO_MVP.md#gestão-de-custos), `routers/costs.py`, `pages/Costs.tsx` |
| Front-end, back-end e banco de dados | React com TypeScript, FastAPI, SQLAlchemy e Alembic, PostgreSQL em produção | [README.md](../../README.md) |
| Modelo relacional (DER/SQL) | **Novo em 06/10/2026.** DER gerado dos modelos, com o SQL nas migrações | [der.md](der.md) |
| Código versionado e rastreável | Hook e CI exigem a chave do card no commit desde 06/10/2026 | [CONTRIBUTING.md](../../CONTRIBUTING.md) |
| Jira e Confluence | Projeto `VEL` com 55 cards: 13 épicos, 33 histórias e 9 tarefas. Espaço `VELOUR` com 5 páginas. O espaço pessoal tem mais 8 páginas, de 18/08, com requisitos, protótipo e fluxo de telas, plano de testes e manual. | [matriz-alinhamento.md](matriz-alinhamento.md) |
| Figma | Protótipo no Figma Make, com link na página "Cronograma e status das entregas" do Confluence desde 29/09/2026. O arquivo é privado e não foi aberto nesta revisão. | [prototipo-figma-telas.md](prototipo-figma-telas.md) |

## Pontuação por Épico (Pódio)

Cada Épico vale até 100 pontos. O ranking acumulado dá bônus na nota da Banca Final: +30% para o 1º lugar, +20% para o 2º e +10% para o 3º.

| Critério | Pontos | O que conta | Situação do Velour em 06/10/2026 |
|---|---|---|---|
| Pontualidade & Tasks | 20 | Histórias e tarefas no prazo do Épico, vídeos enviados por e-mail com link do Google Drive | Depende do grupo. A 1ª entrega teve nota 0,0, registrada pela professora em 17/08. |
| Documentação & Canvas | 20 | Confluence atualizado, regras de negócio e critérios de aceite das histórias | As histórias têm descrição no formato "Como…, quero…". VEL-11, VEL-12, VEL-13, VEL-63 e VEL-64 têm seção de critérios de aceite. Outras nove trazem regras em tópicos que servem de critério: VEL-26, 27, 28, 31, 33, 36, 41, 42 e 48. A Gestão de Custos está documentada no Confluence desde 06/10. |
| Qualidade & Padrão de Código | 30 | Repositório funcional, com commits rastreáveis às chaves do Jira (`PI6-XX`) | Código testado. Os commits até 29/09 **não** têm chave. A partir de 06/10, o hook e a CI exigem a chave `VEL-<número>`. Veja a nota sobre `PI6` abaixo. |
| Fidelidade UI/UX (Figma) | 15 | Figma aderente à proposta e usável | Há protótipo no Figma Make, ligado no Confluence. Não consegui abri-lo, então não sei se cobre a aba Custos, criada em 06/10. |
| Evolução nas Mentorias | 15 | Feedbacks da professora absorvidos | Depende do grupo. |

**Chave `PI6` ou `VEL`.** O guia usa `PI6-12` como exemplo de chave, mas o projeto do grupo no Jira usa `VEL`. A verificação aceita `VEL`, e `JIRA_PROJECT_KEYS=PI6,VEL` faz aceitar as duas. Confirme com a professora se a chave `PI6` é obrigatória. Se for, mude a chave do projeto no Jira, em Configurações do projeto → Detalhes. As chaves antigas continuam redirecionando.

## Cronograma e situação

Datas de segunda (T.A) e terça (T.B). Os "Épicos" do guia são fases da disciplina e não coincidem com EP01 a EP12 do Jira. A página de cronograma do Confluence já explica isso.

| Aula | Data | Etapa | Entregável do guia | Situação em 06/10/2026 |
|---|---|---|---|---|
| 01 | 27/07 | Setup I | Apresentação do bootcamp e do Pódio | Não se aplica. |
| 02 | 28/07 | Setup II | Contas no Jira, Confluence e Figma; organização no GitHub | Jira, Confluence e GitHub existem. O link do Figma Make entrou no Confluence em 29/09. |
| 03 | 03/08 | Setup III (Entrega 1) | Escopo transcrito para Jira, Confluence e Figma, com o backlog | Backlog no Jira e páginas no Confluence. O link do Figma só entrou em 29/09. |
| 04 | 04/08 | Setup IV | Metodologia ágil e entregas em sprints no Jira | **O projeto `VEL` não tem quadro nem sprints.** O único quadro do site é do projeto `KAN`. |
| 05 | 10/08 | Épico 1, Sprint 1 (Entrega 2) | Telas no Figma; requisitos e histórias no Confluence e no Jira | Histórias no Jira. Requisitos na página "03 — Levantamento de Requisitos" e telas em "5- Protótipo e Fluxo de Telas", ambas no espaço pessoal do Confluence. Protótipo no Figma Make. |
| 06 | 11/08 | Épico 2, Sprint 1 | DER e SQL do banco; vídeo parcial no Google Drive | Banco e migrações existem. DER criado em 06/10, em [der.md](der.md). Vídeo parcial não consta no repositório. |
| 07 | 17 e 18/08 | Épico 2, Sprint 1 (Entrega 3) | Tabelas SQL e carga inicial de teste | Migrações Alembic e `seed.py`. |
| 08 | 24 e 25/08 | Épico 2, Sprint 2 | APIs, autenticação, controle de acesso e regras de Financeiro, Contabilidade e Custos | APIs, autenticação e papéis existem. Custos implementado em 06/10. |
| 09 | 31/08 e 01/09 | Épico 2, Sprint 2 | Sincronizar Jira e Confluence | Feito em 29/09. Veja o [README](README.md). |
| 10 | 14 e 15/09 | Preparação P1 | Screencast de 3 a 5 minutos | Há um vídeo de 2min30, sem telas do Jira, do Confluence ou do Figma. |
| P1 | 21 e 22/09 | Prova do 3º bimestre (60% da nota) | Link do vídeo e pitch parcial | VEL-53 está como Concluído. |
| 11 | 28 e 29/09 | Épico 3, Sprint 1 | Telas consumindo a API, com layouts e cadastros | Todas as telas consomem a API. |
| 12 | 05 e 06/10 | Épico 3, Sprint 2 | Painel financeiro com indicadores, relatórios e acessibilidade | Já havia Dashboard, Relatórios e Financeiro. Em 06/10 entraram o painel de custos, com orçamento e alertas, o CSV e o atalho "Pular para o conteúdo". |
| 13 | 19 e 20/10 | Épico 3, Sprint 3 (Entrega 4) | Testes de ponta a ponta, correção de bugs, commits do GitHub ligados ao Jira e envio do vídeo | Vídeo de 4 minutos gravado e, segundo o usuário, enviado em 06/10, adiantado em relação a esta data; está em [video/velour-demonstracao.mp4](video/velour-demonstracao.mp4). Há testes de API e de componentes, mas não suíte de ponta a ponta no navegador. A ligação GitHub–Jira depende do grupo. |
| 14 | 26 e 27/10 | Preparação | Alinhar Confluence, Jira e artigo | Pendente. Rascunho do artigo em [artigo-cientifico.md](artigo-cientifico.md). |
| — | 09 e 10/11 | Pré-Banca Interna | Software completo, auditoria de código e governança | Pendente. |
| — | 16 e 17/11 | Banca Coordenador | Validação com a coordenação | Pendente. |
| — | 23 e 24/11 | Banca Final | Defesa pública, com o bônus do Pódio | Pendente. Roteiro em [roteiro-banca.md](roteiro-banca.md). |

As tarefas VEL-53 a VEL-61 do Jira seguem os e-mails da professora, não este guia. Por exemplo, VEL-54 marca "vídeo + apresentação" para 05 e 06/10, enquanto o guia marca a Sprint 2 do Épico 3 para essas datas e a Entrega 4 para 19 e 20/10. A página de cronograma do Confluence usa uma terceira numeração: Épico 3 para Financeiro, 4 para Fiscal e 5 para Contábil. O grupo precisa decidir qual calendário vale e alinhar o Jira e o Confluence.

## Vídeo de demonstração

O guia exige de 3 a 5 minutos para o vídeo da P1, e a Entrega 4 também pede vídeo. Proposta para o próximo, usando a estrutura do guia:

| Tempo | Trecho do guia | O que mostrar no Velour |
|---|---|---|
| 0:00 a 0:30 | Abertura | Grupo, problema dos salões e proposta do Velour como SaaS com Financeiro, Contabilidade e Custos. |
| 0:30 a 1:30 | Jira & Confluence | Quadro do Jira com cards em Concluído e em andamento, e uma história com critérios de aceite. Página de requisitos no Confluence. Um card com o commit vinculado. |
| 1:30 a 2:30 | Figma | Protótipo do Figma Make: Dashboard, Financeiro e aba Custos. Acrescente a aba Custos se ela ainda não estiver no protótipo. |
| 2:30 a 4:30 | Software funcional | Telas em código com dados gravados no banco. Registre uma despesa, abra Custos e mostre os custos fixos atualizados. Defina um orçamento abaixo do realizado, salve, recarregue a página e mostre o alerta. Mostre a DRE do mesmo mês e o mesmo resultado. |
| Entrega | Google Drive | Vídeo no Drive, link enviado por e-mail à professora. |

Requisitos para gravar: um quadro do Jira para o projeto `VEL` e cards em mais de uma coluna. Hoje há só "Tarefas pendentes" e "Concluído", sem quadro.

## Regras de ouro

| Regra | Situação |
|---|---|
| Nenhum commit sem a chave do card do Jira | Atendida a partir de 06/10/2026: o hook em `.githooks/commit-msg` e o job "Commit traceability (Jira)" da CI recusam commit sem chave. Cada clone ativa o hook com `git config core.hooksPath .githooks`. O histórico anterior não foi reescrito. |
| Definição de pronto: só vai para Done o que funciona, foi testado e está documentado no Confluence | **Parcial.** Os cards da Gestão de Custos (VEL-62 a VEL-64) só foram para Concluído depois da documentação no Confluence. VEL-55 a VEL-58, VEL-60 e VEL-61 continuam em Concluído com datas futuras, até 24/11, como o usuário pediu em 29/09. |
| Pontualidade | Depende do grupo. |

## Jira e Confluence em 06/10/2026

Atualizados com o mínimo para atender ao guia, a pedido do usuário:

- **Jira:** criados o épico VEL-62 (EP13 — Gestão de Custos) e as histórias VEL-63 (painel de custos e ponto de equilíbrio) e VEL-64 (orçado × realizado com alertas), com critérios de aceite, todos em Concluído. VEL-11, VEL-12 e VEL-13 ganharam descrição e critérios de aceite. Depois, VEL-54 (vídeo e apresentação) foi para Concluído, e foram criados VEL-65 (Entrega 4, de 19 e 20/10) e VEL-66 (atualizar o protótipo no Figma Make com a aba Custos), ambos pendentes.
- **Confluence:** a página de módulos passou a se chamar "Módulos Financeiro, Custos, Fiscal e Contábil" e ganhou a seção 4, Gestão de Custos. O cronograma ganhou a linha da Gestão de Custos, e a visão geral, o épico VEL-62, o DER e o padrão de commits. A página inicial cita o módulo e o link do Figma Make.
- Os commits de código de 06/10 citam épicos que já existiam: VEL-22 (Módulo Financeiro) para custos, VEL-20 (Dashboard e Relatórios) para acessibilidade e VEL-25 (Entregas Acadêmicas) para governança e documentação. Os próximos sobre custos devem citar VEL-62, VEL-63 ou VEL-64.

## O que depende do grupo

1. Ter um quadro com coluna "Em andamento" para o vídeo. O `VEL` é um projeto de negócios (Jira Work Management), que não tem sprints e só tem os status "Tarefas pendentes" e "Concluído". Na visualização Quadro do projeto, dá para acrescentar a coluna "Em andamento". Sprints de verdade exigiriam um projeto de software, e mover os cards trocaria as chaves `VEL` citadas nos commits. Tarefas com data futura em Concluído contrariam a definição de pronto do guia.
2. Acrescentar critérios de aceite às histórias que só têm a descrição, se a professora cobrar.
3. Instalar o aplicativo *GitHub for Jira* para os commits aparecerem nos cards. É exigido na Entrega 4.
4. Compartilhar o protótipo do Figma Make com a professora, conferir se ele cobre a aba Custos e linkar também nos cards do Jira. Os 8 documentos do espaço pessoal do Confluence só valem como evidência se a professora tiver acesso a eles.
5. Se a professora exigir a tela real do Jira, do Confluence ou do Figma, gravar esses trechos e substituir no vídeo. O vídeo foi enviado em 06/10, segundo o usuário.
6. Confirmar com a professora a chave `PI6` e qual calendário vale, o do guia ou o dos e-mails.
7. Ativar o hook de commits em cada clone.
