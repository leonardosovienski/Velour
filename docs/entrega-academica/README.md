# Entrega acadêmica — Projeto Integrador VI

Material de apoio para atender os pedidos da professora Kátia Arruda dos Santos Packer (UNIFACEAR), recebidos por e-mail em 05/08, 11/08, 17/08, 08/09 e 18/09/2026. Tudo aqui parte do repositório Velour e dos registros do Jira (projeto `VEL`) e do Confluence (espaço `VELOUR`). Nada foi enviado à professora: o envio e as escolhas do grupo dependem de quem assina.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| [guia-da-disciplina.md](guia-da-disciplina.md) | Exigências do guia da disciplina, cronograma, critérios do Pódio e situação do Velour em 06/10/2026. |
| [der.md](der.md) | Diagrama entidade-relacionamento do banco, gerado dos modelos. |
| [resposta-email-professora.md](resposta-email-professora.md) | Rascunho da resposta ao e-mail de 08/09, com campos a preencher. |
| [artigo-cientifico.md](artigo-cientifico.md) | Rascunho do artigo exigido na Banca Final. |
| [roteiro-banca.md](roteiro-banca.md) | Roteiro de demonstração, checklist e perguntas prováveis da banca. |
| [prototipo-figma-telas.md](prototipo-figma-telas.md) | Especificação das telas para montar o protótipo no Figma. |
| [matriz-alinhamento.md](matriz-alinhamento.md) | Épicos do Jira, páginas do Confluence, código e telas lado a lado, com as divergências. |
| [correcao-confluence.md](correcao-confluence.md) | Texto pronto para corrigir a página de cronograma no Confluence. |

## Vídeo e apresentação

- **Apresentação:** 13 slides na identidade visual do Velour, publicados como artefato privado em https://claude.ai/artifact/5u8FDuwNVet9WiFJ8q75fv. Só o dono abre o link até ele ser compartilhado. Os campos entre colchetes, como nomes do grupo, data da banca e link do Figma, precisam ser preenchidos.
- **Vídeo de 06/10/2026:** [video/velour-demonstracao.mp4](video/velour-demonstracao.mp4), enviado à professora no mesmo dia, segundo o usuário. Tem 4 minutos, sem som, legendas na tela e dados fictícios do `seed.py`. A versão atual traz na abertura o autor, Leonardo Sanches Sovienski, num projeto individual, e mostra no quadro do Jira os cards VEL-65 e VEL-66, criados depois do envio. Segue a estrutura do guia: abertura (0:00), Jira e Confluence (0:24), Figma (1:15), software funcionando (1:27) e qualidade de código (cerca de 3:15). No software, mostra uma despesa gravada, o orçamento salvo e mantido ao recarregar a página, o alerta de orçamento estourado, a DRE com o mesmo resultado da gestão de custos, o atalho de acessibilidade e a tela no celular. Na qualidade, mostra o `git commit` sem chave recusado e os testes.
- **O que esse vídeo não tem:** a tela real do Jira, do Confluence e do Figma. Os cards, as histórias e a página aparecem com o conteúdo real lido pela API, no visual do Velour. Do Figma aparecem o link e a interface do sistema, porque o arquivo é privado. Se a professora exigir a tela das ferramentas, grave esses trechos e substitua o intervalo de 0:24 a 1:27.
- **Vídeo anterior:** 2 minutos e 30 segundos, sem voz, fora do repositório.

## Pedidos da professora e situação

| Pedido | Origem | Situação |
|---|---|---|
| Responder confirmando ciência e a escolha sobre a gamificação, copiando o grupo e o coordenador Márcio | E-mail de 08/09, prazo 11/09 | Rascunho pronto. O prazo já venceu. Falta a escolha do grupo e os endereços. |
| Acompanhar a gamificação: grupo de WhatsApp, entregas por Épico com vídeo e defesa presencial | E-mails de 08/09 e 18/09 | Vale só se o grupo estiver entre os confirmados: G1, G2, G6, G7, G8, G10, G11, G12, G14, G17 e G18. |
| Apresentar o sistema em pleno funcionamento, com código-fonte | Banca Final | Sistema verificado e instalação limpa corrigida. Roteiro pronto. |
| Comprovar Jira, Confluence e Figma alinhados ao código | E-mails de 05/08 e 08/09 | Jira e Confluence existem. O protótipo no Figma Make está ligado na página de cronograma do Confluence desde 29/09, mas é privado e não foi conferido. |
| Apresentar o artigo científico nas normas da instituição | E-mail de 08/09 | Rascunho estruturado. Faltam autores, modelo da instituição e conferência das referências. |
| Ler os materiais anexados | E-mails de 05/08 e 11/08 | O guia da disciplina foi lido em 06/10/2026, a partir de fotos das páginas, e está em [guia-da-disciplina.md](guia-da-disciplina.md). Outros anexos, se houver, continuam sem leitura. |

## Rodada de 06/10/2026: guia da disciplina

O guia da disciplina chegou em fotos e está transcrito em [guia-da-disciplina.md](guia-da-disciplina.md). As lacunas que podiam ser resolvidas no código foram fechadas nesta rodada.

**No repositório:**
- **Gestão de Custos**, que o guia exige ao lado de Financeiro e Contabilidade. É a aba Custos do Financeiro, com indicadores, ponto de equilíbrio, orçado × realizado, alertas, margens por serviço e por profissional, custo-padrão da ficha técnica, evolução de seis meses e CSV. O orçamento fica na tabela nova `cost_budgets`, da migração `a7b8c9d0e1f2`. Detalhes em [FINANCEIRO_MVP.md](../../FINANCEIRO_MVP.md#gestão-de-custos). Captura em [telas/admin-financeiro-custos.png](telas/admin-financeiro-custos.png).
- **Commits com a chave do Jira**, a regra de ouro do guia. O hook `.githooks/commit-msg` e o job "Commit traceability (Jira)" da CI recusam commit sem `VEL-<número>`. Veja [CONTRIBUTING.md](../../CONTRIBUTING.md).
- **Acessibilidade**, pedida na Aula 12. Atalho "Pular para o conteúdo" no primeiro Tab, e o overlay do menu móvel foi ocultado dos leitores de tela. As abas Custos e Contábil deixaram de estourar a largura em celulares de 390 px. Na Contábil, o problema já existia.
- **DER** gerado dos modelos, em [der.md](der.md), pedido na Aula 06.
- Correção de duas vulnerabilidades altas em dependências de desenvolvimento do frontend: `brace-expansion` e `source-map-js`. O `npm audit` já falhava na `main`. A correção usou `npm audit fix` e só mudou versões patch.
- Documentação: manual, Financeiro, artigo (seção 4.5), especificação do Figma, roteiro da banca e matriz de alinhamento.

**Verificações executadas**, num contêiner Linux com Python 3.13.16, Node 22.22.0, npm 10.9.4 e PostgreSQL 16 descartável. A CI usa Node 24 e PostgreSQL 17, então o resultado não substitui a CI.

| Verificação | Resultado |
|---|---|
| Backend, `pytest tests/` com SQLite em memória e aviso do SQLAlchemy tratado como erro | 239 aprovados e 7 pulados, que são a suíte PostgreSQL |
| Suíte PostgreSQL com `TEST_POSTGRES_URL` | 7 aprovados, incluindo o relatório de custos e a restrição única do orçamento |
| Migrações em PostgreSQL | Subida até `f2a3b4c5d6e7`, depois até `a7b8c9d0e1f2`, descida e nova subida. `alembic check` sem divergências. |
| Migrações em SQLite, mesmo fluxo da CI | `upgrade c4f1a9d7e2b0`, `downgrade base`, `upgrade head` e `check`, sem divergências |
| `pip-audit -r requirements.txt` | Nenhuma vulnerabilidade conhecida |
| Frontend: `npm ci`, `npm run lint` e `npm run build` | Aprovados. Pacote inicial de 325,26 kB, 105,02 kB com gzip. |
| Frontend, `npm run test` | 62 aprovados em 18 arquivos |
| `npm audit --audit-level=high` | Nenhuma vulnerabilidade, depois da correção |
| Hook de commit | Recusa mensagem sem chave e aceita `VEL-<número>: descrição` |
| Navegador (Chromium) com dados do `seed.py` | As sete abas do Financeiro aparecem. O orçamento salvo persiste depois de recarregar, e a linha estourada gera alerta. O primeiro Tab foca o atalho, e o Enter leva ao conteúdo. A 390 px não há rolagem horizontal em Custos, Contábil, Visão geral e Recebimentos. Sem erros de console. |
| API com dados do `seed.py` | O resultado de setembro na gestão de custos, R$ 400,00, é igual ao da DRE. |

Não executado: containers e backup com restauração, porque o Docker não tem daemon neste ambiente, e o job novo da CI, que só roda num pull request. Também ficaram de fora a migração de uma base com dados reais e a navegação como gerente ou profissional pela interface. A API foi testada para profissional, com resposta 403.

**Fora do repositório**, tudo depende do grupo e está listado em [guia-da-disciplina.md](guia-da-disciplina.md#o-que-depende-do-grupo): coluna "Em andamento" no quadro do `VEL`, GitHub for Jira, compartilhamento do Figma Make e tela de Custos nele, e a confirmação da chave `PI6`. O vídeo já foi enviado. No Jira e no Confluence, a pedido do usuário, entrou só o mínimo: épico VEL-62 e histórias VEL-63 e VEL-64, critérios de aceite em VEL-11 a VEL-13 e a Gestão de Custos nas páginas do espaço `VELOUR`. Detalhes em [guia-da-disciplina.md](guia-da-disciplina.md#jira-e-confluence-em-06102026).

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
| Frontend, `npm run test` | 56 testes aprovados em 16 arquivos, incluindo o teste da correção descrita abaixo. |
| Frontend, `npm run build` | Concluído. Pacote inicial de 324,99 kB, 104,97 kB com gzip. |
| Frontend, `npm audit --audit-level=high` | Nenhuma vulnerabilidade. |

| Navegador (Chromium), login como administrador e 16 telas | Todas carregaram, sem falha de API. O único erro de console foi de certificado, provavelmente de recurso externo bloqueado pelo proxy. Capturas em [telas](telas). |
| API contra os dados do `seed.py` | Conflito de agenda 409, horário adjacente 201, data com fuso 422. Conclusão com 100 pontos resultou em R$ 143, repetição 409 sem repetir pontos. Profissional vê só a própria agenda e recebe 403 em estoque, relatórios, fidelidade, usuários e indicações. Sem token, 401. |

Não executado: containers e backup com restauração, porque o Docker não tem daemon neste ambiente. Também não foram testadas a migração a partir de uma base existente, a navegação como profissional pela interface e a interação manual com formulários e modais. A verificação usou um banco SQLite descartável criado pelo `seed.py`, só em desenvolvimento. Stripe e SMTP não foram homologados com credenciais reais.

## Correções feitas nesta rodada

**No repositório:**
- O formulário de conclusão de atendimento tinha um defeito. O campo "Valor recebido" exibia o valor final como sugestão, mas não o guardava. Quem marcava "Pagamento recebido", escolhia a forma de pagamento e aceitava a sugestão recebia o erro "Informe a forma de pagamento e o valor recebido". Agora a sugestão exibida é enviada. Um teste novo cobre o caso e falha sem a correção. Foi descoberto ao gravar o vídeo da demonstração.
- O TypeScript voltou para a série 6.0. A versão 7.0.2, aceita pelo Dependabot no commit `d651f68`, quebrava `npm ci` e `npm run lint` porque o typescript-eslint só aceita versões abaixo da 6.1. O `package-lock.json` foi regenerado.
- O Dependabot agora ignora saltos de versão major do TypeScript, até o typescript-eslint suportar a versão 7.
- Um aviso do SQLAlchemy em `routers/reports.py`, sobre o uso de uma subconsulta em `IN`, foi corrigido sem mudar o resultado. Os testes continuam aprovados em SQLite e PostgreSQL, com esse aviso tratado como erro.

**No Jira:**
- Primeiro, as tarefas de 05/10 a 24/11 foram devolvidas a "Tarefas pendentes", por ainda não terem acontecido. Depois, a pedido do usuário, VEL-55, VEL-58, VEL-60 e VEL-61 foram movidas de volta para Concluído em 29/09/2026. O Jira passou a mostrar como concluídas, incluindo a Banca Final de 23 e 24/11, tarefas com data futura.
- VEL-15 passou de Tarefa para História.

**No Confluence:** a página "Cronograma e status das entregas" foi corrigida na versão 3 e depois alinhada ao Jira na versão 4, com autorização do usuário. O texto cita o projeto `VEL`, e a coluna de situação espelha o Jira: tudo Concluído, exceto VEL-54 e VEL-59. A lista de entrega final continua desmarcada, porque vídeo, apresentação e artigo não estão prontos. O texto da versão 3 está em [correcao-confluence.md](correcao-confluence.md).

## O que não consegui corrigir

A permissão do ambiente negou estas ações, mesmo depois da autorização do usuário. Elas ficam com você:

- **Jira:** mover VEL-54 e VEL-59 para Concluído. Continuam em "Tarefas pendentes".
- **Confluence:** nada pendente na coluna de situação, que já espelha o Jira. Só a lista de entrega final segue desmarcada, e cabe a você marcá-la quando vídeo, apresentação e artigo existirem.
- **Figma:** não tenho acesso ao Figma. O link do protótipo no Figma Make foi acrescentado depois, na versão 5 da página de cronograma do Confluence.
- **Envio do e-mail à professora:** depende de escolhas do grupo.

## Pontos que dependem do grupo

- **Datas.** O e-mail de 05/08 cita "segunda-feira, dia 11/08", mas 11/08/2026 foi terça. O e-mail de 17/08 fixa o prazo final em sexta, 14/08.
- **1ª Entrega.** A professora registrou nota 0,0 em 17/08. Nada aqui altera isso.
- **PDFs anexos.** Os materiais da professora não estavam acessíveis e podem trazer exigências que não constam aqui.
