# Roteiro da Banca Final

A Banca Final está no Jira para 23 e 24/11/2026. A duração da apresentação não consta nos e-mails lidos. O roteiro abaixo supõe cerca de 12 minutos e pode ser cortado. A professora também exige, na primeira entrega, vídeo de até 5 minutos com Confluence, Jira e Figma. O trecho 2 serve de base para esse vídeo.

## Antes da banca

1. Confirme, numa cópia limpa do repositório, que `npm ci`, `npm run lint`, `npm run test` e `npm run build` passam em `frontend/`. Passaram em 29/09/2026 depois da correção do TypeScript. Veja [README.md](README.md).
2. Prepare um banco descartável de desenvolvimento e rode `alembic upgrade head`. Crie os dados com `seed.py`, que só roda em desenvolvimento e recria o salão `demo`. As credenciais de demonstração estão no próprio `seed.py`. Nunca use dados reais.
3. Confira o Jira e o Confluence. O Jira mostra a maioria das tarefas de outubro e novembro como concluídas, e o Confluence as mostra como pendentes. Decida qual é o estado real antes de a professora comparar. Veja [matriz-alinhamento.md](matriz-alinhamento.md) e [correcao-confluence.md](correcao-confluence.md).
4. Deixe abertos: Jira, Confluence, Figma, o repositório, o sistema em `http://localhost:5173` e um terminal.
5. Rode os testes uma vez antes, para conhecer o tempo. O backend levou cerca de 30 segundos.

## Roteiro

| Tempo | Trecho | O que mostrar |
|---|---|---|
| 0:00 a 1:00 | 1. Problema e proposta | O que o Velour resolve, quem usa e o que não faz. Diga logo que fiscal e contábil são demonstrativos. |
| 1:00 a 3:00 | 2. Gestão e documentação | Quadro do Jira com os 12 épicos e uma história com critérios de aceite. Espaço `VELOUR` no Confluence. Protótipo no Figma. Mostre a rastreabilidade em [matriz-alinhamento.md](matriz-alinhamento.md). |
| 3:00 a 4:30 | 3. Arquitetura e código | Diagrama da seção 4.1 do [artigo](artigo-cientifico.md). Pastas `routers`, `models`, `schemas` e `frontend/src/pages`. Onde fica o escopo por salão em `database.py`. |
| 4:30 a 9:30 | 4. Demonstração ao vivo | Sequência abaixo. |
| 9:30 a 10:30 | 5. Qualidade | Rodar `python -m pytest tests/` e mostrar o resultado. Explicar que os testes PostgreSQL só rodam com base configurada. |
| 10:30 a 12:00 | 6. Limites e próximos passos | Fiscal e contábil demonstrativos, Stripe e SMTP sem homologação real, uma réplica da API, sem portal do cliente. |

### Exemplo verificado com o seed atual

Em 29/09/2026, com os dados de `seed.py`, a conclusão de um serviço de R$ 180,00 para um cliente Platinum, resgatando 100 pontos, resultou em R$ 143,00. O desconto do nível foi de R$ 27,00 e o resgate valeu R$ 10,00. Repetir a conclusão retornou 409 e não alterou os pontos. Os valores dependem dos dados gerados, então confirme antes da banca. As capturas das telas com esses dados estão em [telas](telas).

### Sequência da demonstração

1. **Login como administrador.** Abra o Dashboard, com agenda do dia, receita e alertas.
2. **Cadastros.** Mostre um serviço com ficha técnica de insumos e o estoque correspondente.
3. **Agenda.** Crie um atendimento e tente outro no mesmo horário para o mesmo profissional. A API recusa com 409. Crie um adjacente, que é aceito.
4. **Conclusão.** Conclua um atendimento de cliente com pontos, resgatando 100 pontos. Mostre o desconto do nível, o teto de 50% e o pagamento registrado.
5. **Efeitos.** Abra o perfil do cliente para ver pontos e nível. Volte ao estoque para ver a baixa. Tente concluir de novo e mostre que não repete os efeitos.
6. **Financeiro.** Recebimentos, despesas e resumo do mês. Em seguida o Contábil, com DRE e download do PDF, e os Documentos fiscais, com emissão simulada.
7. **Permissões.** Entre como profissional e mostre que só a própria agenda aparece. O menu esconde Relatórios e Usuários, mas ainda lista Estoque e Financeiro. Abra uma dessas telas para mostrar que a API nega o acesso, e explique que a autorização está no servidor, não no menu.
8. **Isolamento.** Mostre no teste `test_tenancy.py` o acesso negado a dados de outro salão, em vez de criar um segundo salão ao vivo.
9. **Assinatura.** Abra `/billing` e explique o teste de 14 dias e o bloqueio por 402.

## Perguntas prováveis

| Pergunta | Resposta apoiada no projeto |
|---|---|
| Como você garante que um salão não vê os dados de outro? | Sessão com escopo de salão definido pela autenticação, coluna de salão em todo registro operacional e restrições compostas no banco. Testes cobrem listas, escritas, IDs e fotos de outro salão. |
| O cliente pode forjar o salão na requisição? | Não. O escopo vem do token e do banco, nunca de um campo enviado pelo cliente. |
| O Stripe está em produção? | Não. Há implementação e testes locais, sem homologação com credenciais reais. |
| A nota fiscal é válida? | Não. É demonstração acadêmica, sem transmissão à Receita ou à prefeitura. |
| Como evita dois agendamentos simultâneos no mesmo horário? | A regra de conflito é validada no servidor, e as mutações concorrentes são serializadas por travas de domínio, com teste específico. |
| Por que só uma réplica da API? | Travas, limites de requisição e agendadores são locais ao processo. Um bloqueio consultivo no PostgreSQL impede uma segunda API. Escalar exige redesenhar esses pontos. |
| Um atendimento concluído pode ser refeito? | Não. Repetir a conclusão retorna conflito, e encerrados não reabrem por status. |
| O que falta para vender? | Homologar Stripe e SMTP, HTTPS e infraestrutura, backup externo, monitoramento e validar com salões reais. |
| E o teste de segurança? | Há testes de autorização, revogação de sessão e limites de requisição. Não houve auditoria externa. |
