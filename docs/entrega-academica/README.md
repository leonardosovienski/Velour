# Entrega acadêmica — Projeto Integrador VI

Material de apoio para atender os pedidos da professora Kátia Arruda dos Santos Packer (UNIFACEAR), recebidos por e-mail em 05/08, 11/08, 17/08, 08/09 e 18/09/2026. Tudo aqui parte do repositório Velour e dos registros do Jira (projeto `VEL`) e do Confluence (espaço `VELOUR`). Nada foi enviado à professora: o envio e as escolhas do grupo dependem de quem assina.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| [resposta-email-professora.md](resposta-email-professora.md) | Rascunho da resposta ao e-mail de 08/09, com campos a preencher. |
| [artigo-cientifico.md](artigo-cientifico.md) | Rascunho do artigo exigido na Banca Final. |
| [roteiro-banca.md](roteiro-banca.md) | Roteiro de demonstração, checklist e perguntas prováveis da banca. |
| [prototipo-figma-telas.md](prototipo-figma-telas.md) | Especificação das telas para montar o protótipo no Figma. |
| [matriz-alinhamento.md](matriz-alinhamento.md) | Épicos do Jira, páginas do Confluence, código e telas lado a lado, com as divergências. |
| [correcao-confluence.md](correcao-confluence.md) | Texto pronto para corrigir a página de cronograma no Confluence. |

## Pedidos da professora e situação

| Pedido | Origem | Situação |
|---|---|---|
| Responder confirmando ciência e a escolha sobre a gamificação, copiando o grupo e o coordenador Márcio | E-mail de 08/09, prazo 11/09 | Rascunho pronto. O prazo já venceu. Falta a escolha do grupo e os endereços. |
| Acompanhar a gamificação: grupo de WhatsApp, entregas por Épico com vídeo e defesa presencial | E-mails de 08/09 e 18/09 | Vale só se o grupo estiver entre os confirmados: G1, G2, G6, G7, G8, G10, G11, G12, G14, G17 e G18. |
| Apresentar o sistema em pleno funcionamento, com código-fonte | Banca Final | Sistema verificado e instalação limpa corrigida. Roteiro pronto. |
| Comprovar Jira, Confluence e Figma alinhados ao código | E-mails de 05/08 e 08/09 | Jira e Confluence existem. Não há arquivo de Figma no repositório, no Jira nem no Confluence. Especificação pronta para montar. |
| Apresentar o artigo científico nas normas da instituição | E-mail de 08/09 | Rascunho estruturado. Faltam autores, modelo da instituição e conferência das referências. |
| Ler os materiais anexados | E-mails de 05/08 e 11/08 | Não feito. Os PDFs não estavam acessíveis. Podem conter exigências que não constam aqui. |

## Verificações executadas em 29/09/2026

Ambiente: contêiner Linux com Python 3.11.15, Node 22.22.2, npm 10.9.7 e PostgreSQL 16 descartável em `127.0.0.1`. A CI do projeto usa Python 3.12 e 3.13, Node 24 e PostgreSQL 17 em produção, então o resultado não substitui a CI.

| Verificação | Resultado |
|---|---|
| Backend, `pytest tests/` com SQLite em memória | 206 aprovados, 6 pulados. Os pulados são a suíte PostgreSQL. |
| Backend, suíte PostgreSQL com `TEST_POSTGRES_URL` | 6 aprovados. Isolamento entre salões em banco real. |
| Endpoints de telas e relatórios em PostgreSQL | 12 aprovados, junto com a suíte acima, num total de 18. |
| Migrações, `alembic upgrade head` em banco vazio | Concluído até a revisão `f2a3b4c5d6e7`. |
| `alembic check` | Sem divergências entre modelos e migrações. |
| `pip-audit -r requirements.txt` | Nenhuma vulnerabilidade conhecida. |
| Frontend, `npm ci` sem contornos | Concluído. |
| Frontend, `npm run lint` | Aprovado. |
| Frontend, `npm run test` | 55 testes aprovados em 16 arquivos. |
| Frontend, `npm run build` | Concluído. Pacote inicial de 324,99 kB, 104,97 kB com gzip. |
| Frontend, `npm audit --audit-level=high` | Nenhuma vulnerabilidade. |

Não executado: containers, backup e restauração, teste de migração a partir de uma base existente e navegação manual pelas telas. Stripe e SMTP não foram homologados com credenciais reais.

## Correções feitas nesta rodada

**No repositório:**
- O TypeScript voltou para a série 6.0. A versão 7.0.2, aceita pelo Dependabot no commit `d651f68`, quebrava `npm ci` e `npm run lint` porque o typescript-eslint só aceita versões abaixo da 6.1. O `package-lock.json` foi regenerado.
- O Dependabot agora ignora saltos de versão major do TypeScript, até o typescript-eslint suportar a versão 7.
- Um aviso do SQLAlchemy em `routers/reports.py`, sobre o uso de uma subconsulta em `IN`, foi corrigido sem mudar o resultado. Os testes continuam aprovados em SQLite e PostgreSQL, com esse aviso tratado como erro.

**No Jira:**
- VEL-55, VEL-58, VEL-59, VEL-60 e VEL-61 voltaram para "Tarefas pendentes", pois têm datas de 13/10 a 24/11.
- VEL-15 passou de Tarefa para História.

## O que não consegui corrigir

A permissão do ambiente negou estas ações. Elas ficam com você:

- **Jira:** mover VEL-54, VEL-56 e VEL-57 para "Tarefas pendentes". Estão em Concluído, mas têm datas de 05/10, 19/10 e 26/10.
- **Confluence:** editar a página "Cronograma e status das entregas". O texto pronto está em [correcao-confluence.md](correcao-confluence.md).
- **Figma:** o protótipo não existe e não tenho acesso ao Figma.
- **Envio do e-mail à professora:** depende de escolhas do grupo.

## Pontos que dependem do grupo

- **Datas.** O e-mail de 05/08 cita "segunda-feira, dia 11/08", mas 11/08/2026 foi terça. O e-mail de 17/08 fixa o prazo final em sexta, 14/08.
- **1ª Entrega.** A professora registrou nota 0,0 em 17/08. Nada aqui altera isso.
- **PDFs anexos.** Os materiais da professora não estavam acessíveis e podem trazer exigências que não constam aqui.
