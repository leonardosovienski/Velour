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
| Jira e Confluence | Projeto `VEL` com 12 épicos, espaço `VELOUR` com 5 páginas | [matriz-alinhamento.md](matriz-alinhamento.md) |
| Figma | **Não existe.** Especificação pronta para desenhar | [prototipo-figma-telas.md](prototipo-figma-telas.md) |

## Pontuação por Épico (Pódio)

Cada Épico vale até 100 pontos. O ranking acumulado dá bônus na nota da Banca Final: +30% para o 1º lugar, +20% para o 2º e +10% para o 3º.

| Critério | Pontos | O que conta | Situação do Velour em 06/10/2026 |
|---|---|---|---|
| Pontualidade & Tasks | 20 | Histórias e tarefas no prazo do Épico, vídeos enviados por e-mail com link do Google Drive | Depende do grupo. A 1ª entrega teve nota 0,0, registrada pela professora em 17/08. |
| Documentação & Canvas | 20 | Confluence atualizado, regras de negócio e critérios de aceite das histórias | O Confluence não tem página da Gestão de Custos. Os critérios de aceite das histórias do Jira não foram conferidos. Os critérios propostos para os cards de custos estão abaixo. |
| Qualidade & Padrão de Código | 30 | Repositório funcional, com commits rastreáveis às chaves do Jira (`PI6-XX`) | Código testado. Os commits até 29/09 **não** têm chave. A partir de 06/10, o hook e a CI exigem a chave `VEL-<número>`. Veja a nota sobre `PI6` abaixo. |
| Fidelidade UI/UX (Figma) | 15 | Figma aderente à proposta e usável | **Sem protótipo.** É a maior lacuna. |
| Evolução nas Mentorias | 15 | Feedbacks da professora absorvidos | Depende do grupo. |

**Chave `PI6` ou `VEL`.** O guia usa `PI6-12` como exemplo de chave, mas o projeto do grupo no Jira usa `VEL`. A verificação aceita `VEL`, e `JIRA_PROJECT_KEYS=PI6,VEL` faz aceitar as duas. Confirme com a professora se a chave `PI6` é obrigatória. Se for, mude a chave do projeto no Jira, em Configurações do projeto → Detalhes. As chaves antigas continuam redirecionando.

## Cronograma e situação

Datas de segunda (T.A) e terça (T.B). Os "Épicos" do guia são fases da disciplina e não coincidem com EP01 a EP12 do Jira. A página de cronograma do Confluence já explica isso.

| Aula | Data | Etapa | Entregável do guia | Situação em 06/10/2026 |
|---|---|---|---|---|
| 01 | 27/07 | Setup I | Apresentação do bootcamp e do Pódio | Não se aplica. |
| 02 | 28/07 | Setup II | Contas no Jira, Confluence e Figma; organização no GitHub | Jira, Confluence e GitHub existem. Figma não. |
| 03 | 03/08 | Setup III (Entrega 1) | Escopo transcrito para Jira, Confluence e Figma, com o backlog | Backlog no Jira e páginas no Confluence. Sem Figma. |
| 04 | 04/08 | Setup IV | Metodologia ágil e entregas em sprints no Jira | **O projeto `VEL` não tem quadro nem sprints.** O único quadro do site é do projeto `KAN`. |
| 05 | 10/08 | Épico 1, Sprint 1 (Entrega 2) | Telas no Figma; requisitos e histórias no Confluence e no Jira | Histórias RF01, RF05, RF06 e RF14 no Jira. Sem Figma. |
| 06 | 11/08 | Épico 2, Sprint 1 | DER e SQL do banco; vídeo parcial no Google Drive | Banco e migrações existem. DER criado em 06/10, em [der.md](der.md). Vídeo parcial não consta no repositório. |
| 07 | 17 e 18/08 | Épico 2, Sprint 1 (Entrega 3) | Tabelas SQL e carga inicial de teste | Migrações Alembic e `seed.py`. |
| 08 | 24 e 25/08 | Épico 2, Sprint 2 | APIs, autenticação, controle de acesso e regras de Financeiro, Contabilidade e Custos | APIs, autenticação e papéis existem. Custos implementado em 06/10. |
| 09 | 31/08 e 01/09 | Épico 2, Sprint 2 | Sincronizar Jira e Confluence | Feito em 29/09. Veja o [README](README.md). |
| 10 | 14 e 15/09 | Preparação P1 | Screencast de 3 a 5 minutos | Há um vídeo de 2min30, sem telas do Jira, do Confluence ou do Figma. |
| P1 | 21 e 22/09 | Prova do 3º bimestre (60% da nota) | Link do vídeo e pitch parcial | VEL-53 está como Concluído. |
| 11 | 28 e 29/09 | Épico 3, Sprint 1 | Telas consumindo a API, com layouts e cadastros | Todas as telas consomem a API. |
| 12 | 05 e 06/10 | Épico 3, Sprint 2 | Painel financeiro com indicadores, relatórios e acessibilidade | Já havia Dashboard, Relatórios e Financeiro. Em 06/10 entraram o painel de custos, com orçamento e alertas, o CSV e o atalho "Pular para o conteúdo". |
| 13 | 19 e 20/10 | Épico 3, Sprint 3 (Entrega 4) | Testes de ponta a ponta, correção de bugs, commits do GitHub ligados ao Jira e envio do vídeo | Pendente. Há testes de API e de componentes, mas não suíte de ponta a ponta no navegador. Ligação GitHub–Jira e vídeo dependem do grupo. |
| 14 | 26 e 27/10 | Preparação | Alinhar Confluence, Jira e artigo | Pendente. Rascunho do artigo em [artigo-cientifico.md](artigo-cientifico.md). |
| — | 09 e 10/11 | Pré-Banca Interna | Software completo, auditoria de código e governança | Pendente. |
| — | 16 e 17/11 | Banca Coordenador | Validação com a coordenação | Pendente. |
| — | 23 e 24/11 | Banca Final | Defesa pública, com o bônus do Pódio | Pendente. Roteiro em [roteiro-banca.md](roteiro-banca.md). |

As tarefas VEL-53 a VEL-61 do Jira seguem os e-mails da professora, não este guia. Por exemplo, VEL-54 marca "vídeo + apresentação" para 05 e 06/10, enquanto o guia marca a Sprint 2 do Épico 3 para essas datas e a Entrega 4 para 19 e 20/10. O grupo precisa decidir qual calendário vale e alinhar o Jira.

## Vídeo de demonstração

O guia exige de 3 a 5 minutos para o vídeo da P1, e a Entrega 4 também pede vídeo. Proposta para o próximo, usando a estrutura do guia:

| Tempo | Trecho do guia | O que mostrar no Velour |
|---|---|---|
| 0:00 a 0:30 | Abertura | Grupo, problema dos salões e proposta do Velour como SaaS com Financeiro, Contabilidade e Custos. |
| 0:30 a 1:30 | Jira & Confluence | Quadro do Jira com cards em Concluído e em andamento, e uma história com critérios de aceite. Página de requisitos no Confluence. Um card com o commit vinculado. |
| 1:30 a 2:30 | Figma | Protótipo do Dashboard, do Financeiro e da aba Custos. Depende de o protótipo existir. |
| 2:30 a 4:30 | Software funcional | Telas em código com dados gravados no banco. Registre uma despesa, abra Custos e mostre os custos fixos atualizados. Defina um orçamento abaixo do realizado, salve, recarregue a página e mostre o alerta. Mostre a DRE do mesmo mês e o mesmo resultado. |
| Entrega | Google Drive | Vídeo no Drive, link enviado por e-mail à professora. |

Requisitos para gravar: um quadro do Jira para o projeto `VEL` e cards em mais de uma coluna. Hoje há só "Tarefas pendentes" e "Concluído", sem quadro.

## Regras de ouro

| Regra | Situação |
|---|---|
| Nenhum commit sem a chave do card do Jira | Atendida a partir de 06/10/2026: o hook em `.githooks/commit-msg` e o job "Commit traceability (Jira)" da CI recusam commit sem chave. Cada clone ativa o hook com `git config core.hooksPath .githooks`. O histórico anterior não foi reescrito. |
| Definição de pronto: só vai para Done o que funciona, foi testado e está documentado no Confluence | **Não atendida no Jira.** VEL-55 a VEL-58, VEL-60 e VEL-61 estão em Concluído com datas futuras, até 24/11. O épico VEL-22 está concluído, mas a Gestão de Custos não tem página no Confluence. |
| Pontualidade | Depende do grupo. |

## Cards propostos para a Gestão de Custos

Ainda não existem no Jira. Os commits de 06/10 citam épicos existentes: VEL-22 (Módulo Financeiro) para custos, VEL-20 (Dashboard e Relatórios) para acessibilidade e VEL-25 (Entregas Acadêmicas) para governança e documentação. Se o grupo criar os cards abaixo, os próximos commits devem citar as novas chaves.

**Épico: EP13 — Gestão de Custos.** Custeio variável do salão a partir dos registros, com orçamento mensal e alertas.

| História | Critérios de aceite |
|---|---|
| Painel de custos do mês | Dado um mês com atendimentos concluídos e despesas, a aba Custos mostra receita, custos variáveis (insumos, comissões e ISS), margem de contribuição em reais e em percentual, custos fixos e resultado. O ponto de equilíbrio é custo fixo dividido pelo índice de margem. Sem margem positiva, aparece "Não calculável". Sem custos fixos, é zero. Mês sem dados não inventa percentuais. Profissional recebe 403. |
| Orçado × realizado | Gerente ou administrador define o orçamento por linha de custo no mês. Salvar substitui o orçamento inteiro. Valor negativo, linha repetida ou desconhecida retornam 422. Linha acima do orçamento aparece como "Acima do orçamento" e gera alerta. O orçamento de um salão não aparece em outro. |
| Margem por serviço e por profissional | Cada serviço e cada profissional do mês mostra receita, insumos, comissões, ISS e margem. Margem negativa gera alerta. |
| Custo-padrão pela ficha técnica | Cada serviço ativo mostra o custo de insumos da ficha técnica, o ISS e a margem antes da comissão. Preço que não cobre insumos e ISS gera alerta. |
| Relatório de custos em CSV | O download traz indicadores, orçamento, serviços, profissionais e custo-padrão, com `;` e vírgula decimal. Nomes que começam com `=`, `+`, `-` ou `@` não viram fórmula. |

**Tarefas:**
- Commits rastreáveis: hook e verificação na CI.
- Acessibilidade: atalho "Pular para o conteúdo".
- Página "Gestão de custos" no Confluence, a partir de [FINANCEIRO_MVP.md](../../FINANCEIRO_MVP.md#gestão-de-custos).

## O que depende do grupo

1. Criar o quadro Scrum do projeto `VEL`, com as sprints do guia, e mover os cards conforme a definição de pronto. Inclui devolver a pendente as tarefas com data futura.
2. Criar o épico e os cards da Gestão de Custos e a página no Confluence.
3. Instalar o aplicativo *GitHub for Jira* para os commits aparecerem nos cards. É exigido na Entrega 4.
4. Desenhar o protótipo no Figma e linkar no Jira e no Confluence.
5. Gravar o vídeo da Entrega 4 com 3 a 5 minutos e enviá-lo pelo Google Drive.
6. Confirmar com a professora a chave `PI6` e qual calendário vale, o do guia ou o dos e-mails.
7. Ativar o hook de commits em cada clone.
