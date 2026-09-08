# Política de segurança

Esta política orienta relatos de vulnerabilidades e manutenção do Velour. Ela não constitui certificação de segurança, garantia de ausência de falhas, autorização para testar instalações de terceiros ou compromisso de prazo de atendimento.

## Referência para correções

A branch `main` é a referência do código mantido neste repositório. Este documento não estabelece suporte de longo prazo, uma matriz de releases suportadas ou atualização automática das instalações existentes.

Ao relatar um problema, informe o commit ou versão que está usando. Ao implantar uma correção, o operador deve conferir as mudanças, o resultado de CI do commit e a necessidade de migração ou rotação de credenciais. Um problema já corrigido no código pode continuar afetando instalações ainda não atualizadas.

## Como relatar uma vulnerabilidade

Não publique detalhes técnicos de uma vulnerabilidade ainda explorável, provas com dados reais ou segredos em issues, pull requests ou comentários públicos.

Se a aba **Security** do repositório oferecer **Report a vulnerability**, use esse canal privado. A disponibilidade desse recurso depende das configurações do GitHub e não é garantida por este arquivo.

Se não houver essa opção, use um contato privado de suporte ou segurança publicado pelo responsável pela instalação ou pelo mantenedor. Caso nenhum contato privado esteja disponível, abra apenas uma solicitação de canal privado, sem descrever a falha, o alvo ou dados sensíveis. O operador de uma oferta comercial deve publicar um canal de contato monitorado antes de atender clientes.

Um relato útil inclui:

- Commit ou versão, componente e configuração relevante, sem segredos.
- Descrição do problema e impacto observado.
- Passos mínimos para reproduzir com dados fictícios.
- Evidências sanitizadas, como requisições com tokens removidos.
- Informação sobre eventual exposição de dados ou credenciais, sem anexar o material exposto.

Não há SLA de resposta nem programa de recompensa estabelecido neste documento. Relatos devem permitir triagem, reprodução, correção e divulgação coordenada, sem depender de um prazo prometido aqui.

## Escopo técnico

São relevantes para a segurança do Velour:

| Área | Exemplos de problemas |
| --- | --- |
| Isolamento entre salões | Leitura, alteração, exclusão ou vinculação de dados de outra conta |
| Identidade e permissões | JWT, recuperação de senha, revogação, papéis e escopo profissional |
| Cadastro e cobrança | Abuso de cadastro, Checkout duplicado, webhook forjado, liberação indevida de assinatura |
| Arquivos e dados pessoais | Acesso indevido a fotos, path traversal, vazamento em exportações ou logs |
| Regras de negócio | Corridas que alterem saldos, estoque, agendamentos ou fidelidade indevidamente |
| Aplicação e entrega | Frontend, dependências, containers, proxy, CI, configuração e tratamento de segredos |
| Operação | Backups, restauração, acesso privilegiado e exposição de serviços ou credenciais |

Falhas no uso ou na configuração de uma dependência continuam relevantes, mesmo quando a biblioteca é de terceiros. Incidentes do próprio Stripe, provedor de e-mail, hospedagem ou GitHub precisam ser comunicados ao respectivo provedor; problemas na forma como o Velour integra esses serviços também podem ser relatados aqui.

A política não autoriza engenharia social, negação de serviço, acesso a contas de terceiros ou exploração com credenciais obtidas sem autorização. Problemas operacionais de uma instalação podem exigir a participação do seu operador, além de uma correção no repositório.

## Controles atuais e seus limites

O [documento de isolamento](MULTI_TENANCY_PLAN.md) e o [documento de cobrança](ONBOARDING_BILLING_PLAN.md) descrevem os controles implementados. Os limites abaixo importam ao avaliar uma instalação:

- O banco é compartilhado. O escopo das sessões ORM e as constraints de referências separam os salões na aplicação; não há RLS ou separação física de bancos por cliente. Acesso ao banco, ao host ou a `system_scope` é privilegiado.
- Produção exige PostgreSQL, HTTPS na configuração pública e uma única API/worker. A trava de sessão PostgreSQL impede uma segunda API no mesmo banco, mas não transforma os contadores e jobs em serviços distribuídos.
- JWTs ficam em `sessionStorage` e continuam acessíveis a JavaScript da origem. Não há MFA, refresh token ou gerenciamento de dispositivos. Sair da interface remove a credencial local; redefinição de senha e alterações de autorização revogam versões anteriores do token.
- Fotos exigem autenticação e vínculo com o salão/agendamento. A validação de upload usa tipo por assinatura de bytes e tamanho; não inclui antivírus nem inspeção completa de imagens.
- Checkout e portal são hospedados pelo Stripe. A integração verifica assinatura de webhook e consulta o estado atual da assinatura, mas sua operação depende de configuração, disponibilidade e entrega de eventos do provedor.
- Limites de requisição são locais ao processo. E-mails em tarefa de fundo não usam fila durável. Reinícios, entrega de mensagens, backups e monitoração exigem procedimentos operacionais.
- Testes, auditoria de dependências e CI ajudam a detectar regressões. Seus resultados se aplicam ao código e ambiente testados; não equivalem a auditoria independente, teste de intrusão ou certificação regulatória.

Requisitos de implantação e verificações operacionais estão em [PRODUCTION.md](PRODUCTION.md). As condições comerciais e os avisos de privacidade devem refletir a operação real da instalação; não presuma conformidade jurídica apenas pela existência de arquivos no repositório.

## Dados sensíveis e segredos

O sistema pode tratar identificação e contato de clientes, aniversário, alergias, preferências, histórico de atendimento, fotos e informações financeiras. Use dados fictícios em testes e remova dados pessoais das evidências antes de compartilhá-las.

Não inclua no repositório ou em relatos públicos:

- Arquivos `.env`, chaves JWT, senhas, tokens de acesso ou links válidos de recuperação.
- Credenciais de banco, SMTP, Stripe ou outros serviços.
- Bancos, backups, dumps, exportações e uploads de produção.
- Cabeçalhos de autorização, corpos de requisição ou logs contendo segredos e dados de clientes.

As regras do `.gitignore` reduzem commits acidentais, mas não removem arquivos já rastreados nem substituem a revisão do conteúdo. Backups e exports precisam do mesmo cuidado de acesso, armazenamento e retenção que os dados originais.

Se um segredo for exposto, revogue ou rotacione no serviço correspondente. Apagar o arquivo do último commit não invalida cópias existentes. Para JWT, a troca de `SECRET_KEY` invalida os tokens assinados com a chave anterior; para uma conta específica, a aplicação utiliza `token_version`.

## Investigação e resposta

Teste somente ambientes próprios ou com autorização explícita, usando contas e dados fictícios sob seu controle. Para verificar isolamento, crie dois salões de teste em vez de acessar dados de clientes reais. Pare quando houver evidência suficiente e não provoque indisponibilidade deliberada.

O tratamento de um relato deve contemplar avaliação de impacto, reprodução controlada, correção, teste de regressão e orientação para atualização. Quando houver exposição de credenciais, dados ou infraestrutura, o operador deve avaliar também contenção, preservação de evidências e as comunicações aplicáveis ao incidente.

Evite distribuir uma prova de exploração antes que os responsáveis tenham condições de avaliar e corrigir o problema. Não envie cópias de dados pessoais como demonstração: descreva o tipo de exposição e combine o tratamento da evidência por canal privado.
