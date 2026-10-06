# Como contribuir

Leia [CLAUDE.md](CLAUDE.md) para ambiente, invariantes de segurança e verificações antes da entrega.

## Commits rastreáveis ao Jira

Todo commit começa com a chave do card do Jira, dois-pontos e a descrição. O projeto no Jira é `VEL`:

```text
git commit -m "VEL-62: Cria tabela de orçamento de custos"
git commit -m "VEL-62, VEL-63: Liga o orçamento ao painel de custos"
```

Ative a verificação local uma vez por clone:

```text
git config core.hooksPath .githooks
```

O hook `commit-msg` chama [scripts/check_commit_message.py](scripts/check_commit_message.py) e recusa o commit sem chave. A [CI](.github/workflows/ci.yml) aplica a mesma regra a todos os commits de um pull request. Ficam de fora os commits de merge, os reverts gerados pelo Git, `fixup!`/`squash!` e os commits de robôs, como o Dependabot. A variável `JIRA_PROJECT_KEYS` troca as chaves aceitas, por exemplo `JIRA_PROJECT_KEYS=PI6,VEL`.

Para o commit aparecer no card, o Jira precisa estar ligado ao GitHub pelo aplicativo *GitHub for Jira*. Isso é configurado no Jira, não no repositório.

## Definição de pronto

Um card só vai para Concluído quando o código funciona, os testes passam e a mudança está documentada no Confluence e nos Markdown afetados deste repositório.
