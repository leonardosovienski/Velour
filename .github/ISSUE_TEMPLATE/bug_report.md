---
name: "Bug report"
about: "Reporte um problema com passos claros de reprodução"
title: "[BUG] "
labels: ["bug", "triage"]
assignees: []
---

## Resumo

Descreva a falha e o impacto para quem usa o salão.

Não publique senhas, tokens, chaves Stripe/SMTP, arquivos `.env`, dados pessoais ou fotos de clientes. Para suspeita de vulnerabilidade, siga a [política de segurança](https://github.com/leonardosovienski/Velour/blob/main/SECURITY.md) e procure um canal privado antes de divulgar detalhes exploráveis.

## Passos para reproduzir

Use dados fictícios e informe os passos desde o login, o papel do usuário e a tela ou endpoint afetado.

1. Entrar com o papel...
2. Abrir a tela e executar...
3. Observar o resultado...

## Comportamento atual

Inclua a mensagem ou código HTTP recebido e a frequência da falha.

## Comportamento esperado

Descreva o resultado esperado para os mesmos dados.

## Ambiente

- Revisão Git ou versão implantada:
- Sistema operacional e navegador/versão:
- Execução local ou Docker Compose:
- Banco e versão (SQLite de desenvolvimento ou PostgreSQL):
- Papel do usuário (administrador, gerente ou profissional):
- Estado de acesso (teste, ativa, vencida ou suspensa), se relevante:
- Fuso operacional e data/hora da ocorrência, se relevante:

## Evidências

Inclua apenas logs e capturas anonimizados. Se houver falha na CI, informe o link da execução do GitHub Actions. Não anexe um banco comercial.

## Contexto adicional

Informe se começou após atualização e se existe uma forma temporária de contornar a falha.
