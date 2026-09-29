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

## Pedidos da professora e situação

| Pedido | Origem | Situação |
|---|---|---|
| Responder confirmando ciência e a escolha sobre a gamificação, copiando o grupo e o coordenador Márcio | E-mail de 08/09, prazo 11/09 | Rascunho pronto. O prazo já venceu. Falta a escolha do grupo e os endereços. |
| Acompanhar a gamificação: grupo de WhatsApp, entregas por Épico com vídeo e defesa presencial | E-mails de 08/09 e 18/09 | Vale só se o grupo estiver entre os confirmados: G1, G2, G6, G7, G8, G10, G11, G12, G14, G17 e G18. |
| Apresentar o sistema em pleno funcionamento, com código-fonte | Banca Final | Sistema verificado, com ressalvas abaixo. Roteiro pronto. |
| Comprovar Jira, Confluence e Figma alinhados ao código | E-mails de 05/08 e 08/09 | Jira e Confluence existem. Não há arquivo de Figma no repositório, no Jira nem no Confluence. Especificação pronta para montar. |
| Apresentar o artigo científico nas normas da instituição | E-mail de 08/09 | Rascunho estruturado. Faltam autores, modelo da instituição e conferência das referências. |
| Ler os materiais anexados | E-mails de 05/08 e 11/08 | Não feito. Os PDFs não estavam acessíveis. Podem conter exigências que não constam aqui. |

## Verificações executadas em 29/09/2026

Ambiente: contêiner Linux com Python 3.11.15 e Node 22.22.2. A CI do projeto usa Python 3.12 e 3.13 e Node 24, então o resultado não substitui a CI.

| Verificação | Resultado |
|---|---|
| Backend, `pytest tests/` com SQLite em memória | 206 aprovados, 6 pulados. Os pulados são a suíte PostgreSQL, sem `TEST_POSTGRES_URL`. |
| Frontend, `npm run test` | 55 testes aprovados em 16 arquivos. |
| Frontend, `npm run build` | Concluído. Pacote inicial de 324,99 kB, 104,97 kB com gzip. |
| Frontend, `npm ci` | **Falhou** por conflito de dependências. Funcionou com `--legacy-peer-deps`. |
| Frontend, `npm run lint` | **Falhou ao iniciar**. O typescript-eslint não suporta o TypeScript 7.0.2 instalado. |

Não executado: suíte PostgreSQL, migrações com `alembic upgrade` e `alembic check`, `pip-audit`, `npm audit`, containers, backup e restauração. Stripe e SMTP não foram homologados com credenciais reais.

O conflito do `npm ci` e do lint vem da atualização do TypeScript de 6.0.3 para 7.0.2, aceita no commit `d651f68`. Quem clonar o projeto para a banca e seguir o README esbarra nisso. Convém corrigir antes da apresentação.

## Pontos que dependem do grupo

- **Estado do Jira e do Confluence.** Todas as issues do projeto `VEL` estão em Concluído, inclusive as tarefas de 05/10 a 24/11/2026. Hoje é 29/09. O Confluence afirma que todas as fases estão concluídas. Detalhes em [matriz-alinhamento.md](matriz-alinhamento.md).
- **Datas.** O e-mail de 05/08 cita "segunda-feira, dia 11/08", mas 11/08/2026 foi terça. O e-mail de 17/08 fixa o prazo final em sexta, 14/08.
- **1ª Entrega.** A professora registrou nota 0,0 em 17/08. Nada aqui altera isso.
