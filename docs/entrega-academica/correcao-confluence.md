# Correção da página de cronograma no Confluence

A página "Cronograma e status das entregas", no espaço `VELOUR`, tem o identificador 10616833. **Esta correção já foi aplicada em 29/09/2026**, na versão 3, com autorização do usuário. O texto abaixo fica como registro do que foi alterado e serve caso a página precise ser refeita.

## O que está errado

- O texto diz "projeto VELOUR", mas as issues do Jira têm chave `VEL`.
- O painel verde diz "Todas as fases estão concluídas", e todas as linhas de entregas acadêmicas estão em Concluído, inclusive as de 05/10 a 24/11/2026, que ainda não aconteceram.
- Na lista "Entrega final", vídeo, apresentação e artigo estão marcados. O artigo existe só como rascunho em `docs/entrega-academica`, e não há registro do vídeo nem da apresentação.

## O que colocar

**Primeiro parágrafo:**
Cronograma da disciplina e situação de cada fase. As tarefas e prazos estão no Jira, projeto VEL. A numeração "Épico N" da primeira tabela é a da disciplina. Os épicos do Jira vão de EP01 a EP12.

**Painel:** troque o painel verde por um painel azul, de informação.
Concluídos: os módulos do sistema e a Prova P1. As entregas de 05/10 em diante estão pendentes e seguem o calendário da disciplina.

**Coluna Situação, tabela "Entregas acadêmicas":**

| Fase | Jira | Situação correta |
|---|---|---|
| Prova P1, 21/09 e 22/09 | VEL-53 | Concluído |
| Revisão do Projeto, 05/10 a 06/10 | VEL-54 | Pendente |
| Revisão do Artigo, etapa 1, 13/10 | VEL-55 | Pendente |
| Revisão do Artigo, etapa 2, 19/10 e 20/10 | VEL-56 | Pendente |
| Validação do Material, 26/10 e 27/10 | VEL-57 | Pendente |
| Validação Pré-Apresentação, etapa 1, 03/11 | VEL-58 | Pendente |
| Pré-Apresentação, etapa 2, 09/11 e 10/11 | VEL-59 | Pendente |
| Pré-Banca, 16/11 e 17/11 | VEL-60 | Pendente |
| Banca Final, 23/11 e 24/11 | VEL-61 | Pendente |

Use o status cinza "Pendente" nas linhas pendentes.

**Lista "Entrega final":** desmarque as três caixas e escreva o último item como "Artigo, com rascunho no repositório, pasta docs/entrega-academica".

## Jira

O Jira já foi corrigido para VEL-54, VEL-55, VEL-58, VEL-59, VEL-60 e VEL-61. Faltam VEL-56 e VEL-57, que continuam em Concluído. Mova as duas para "Tarefas pendentes". Enquanto isso não for feito, a página do Confluence e o Jira divergem nessas duas linhas.
