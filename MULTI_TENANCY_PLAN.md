# Isolamento entre salões — arquitetura atual

Este documento descreve o núcleo de múltiplos salões implementado no Velour. O nome `MULTI_TENANCY_PLAN.md` foi mantido para preservar os links existentes. A instalação e os requisitos de operação estão em [PRODUCTION.md](PRODUCTION.md); o cadastro e a cobrança estão em [ONBOARDING_BILLING_PLAN.md](ONBOARDING_BILLING_PLAN.md).

## Modelo de implantação

O Velour utiliza um banco compartilhado, com separação lógica das linhas por `tenant_id`. Em produção, o banco deve ser PostgreSQL e a API deve executar em **uma réplica, com um worker**. SQLite serve ao desenvolvimento e aos testes locais.

Cada usuário pertence a um salão. O login usa e-mail globalmente único e emite um JWT com a identificação desse salão. O `slug` é um identificador único de conta; não configura subdomínio, DNS ou roteamento por `Host`. Não há seletor de salão nem associação do mesmo usuário a várias contas.

Não há políticas PostgreSQL de Row-Level Security (RLS), schemas separados ou bancos separados por salão. A aplicação aplica o isolamento de leitura; o banco também impõe integridade das referências entre registros. Credenciais do banco e acesso ao host continuam sendo privilégios globais e precisam de controle operacional.

## Dados e integridade

A entidade [Tenant](models/tenant.py) contém:

| Grupo | Campos |
| --- | --- |
| Identidade | `id`, `name`, `slug`, `created_at` |
| Disponibilidade | `is_active` |
| Assinatura | `subscription_status`, `trial_ends_at`, `current_period_end`, `past_due_since` |
| Vínculo com Stripe | `stripe_customer_id`, `stripe_subscription_id` |
| Checkout | `checkout_session_id`, `checkout_session_expires_at` |
| Aceite dos termos | `accepted_terms_at`, `terms_version` |

O modelo atual não contém CPF/CNPJ, endereço fiscal, plano por usuário ou fuso horário do salão. As datas da conta e da cobrança são gravadas em UTC, sem informação de fuso na coluna.

As seguintes tabelas possuem `tenant_id` obrigatório e indexado: `users`, `clients`, `professionals`, `service_categories`, `services`, `products`, `service_recipes`, `appointments`, `loyalty_transactions`, `referrals`, `stock_movements`, `audit_logs` e `password_reset_tokens`.

As constraints definidas em [models/__init__.py](models/__init__.py) complementam o escopo da aplicação:

- Chave única `(tenant_id, id)` nas tabelas de dados do salão.
- Chaves estrangeiras compostas que exigem o mesmo salão nas referências de negócio, incluindo cliente, profissional, serviço, estoque, indicação, usuário e recuperação de senha.
- Código de cliente e código de indicação únicos dentro do salão: `(tenant_id, code)` e `(tenant_id, referral_code)`.
- E-mail de usuário globalmente único. A aplicação normaliza os e-mails de acesso para minúsculas.

IDs são globais no banco. Os códigos `VLR-...` podem apresentar lacunas; não representam uma sequência contábil contínua. Indicações são consultadas no escopo do salão.

`billing_webhook_events` é um registro global de IDs de eventos processados. Seu acesso exige contexto de sistema e ele não é incluído na exportação do salão.

## Sessões e autenticação

[database.py](database.py) fornece `ScopedSession`, utilizada por `SessionLocal` e pela dependência `get_db`. Uma sessão nova recusa consultas e gravações até receber um escopo válido ou entrar explicitamente em contexto de sistema.

O fluxo de uma requisição autenticada é:

1. [auth.py](auth.py) verifica o JWT e interpreta `sub` e `tenant_id`.
2. `tenant_scope(db, tenant_id)` fixa o salão na sessão compartilhada pelas dependências da requisição. A sessão não pode trocar de salão.
3. A aplicação consulta o usuário ativo, seu vínculo com o salão e a disponibilidade da conta.
4. O `token_version` do JWT deve corresponder ao valor atual do usuário.
5. Os endpoints aplicam, adicionalmente, as permissões do papel e o vínculo profissional quando exigido.

O token contém também e-mail, papel, data de emissão e expiração. A autorização usa o usuário consultado no banco. Redefinir senha, alterar papel/vínculo/situação do usuário ou suspender/restaurar um salão revoga tokens anteriores por `token_version`. Não há refresh token: a sessão expira e o usuário precisa entrar novamente.

O isolamento da sessão cobre consultas ORM de entidades, colunas, agregados, aliases e relacionamentos. Inserções normais recebem automaticamente o `tenant_id` da sessão. Gravações e exclusões de objetos de outro salão, mudanças de titularidade e referências cruzadas são rejeitadas.

Atualizações e exclusões ORM em lote recebem o filtro do salão. Atualizações em lote não podem mudar IDs, titularidade ou chaves estrangeiras. SQL textual, consultas Core, `from_statement`, conexões diretas e caminhos de gravação em lote que contornariam esses controles exigem contexto de sistema.

Para manutenção, autenticação inicial, cadastro, recuperação de conta e cobrança, o código pode usar `system_scope(db)` ou `system_session()`. Esses são acessos privilegiados, não uma opção disponível por parâmetro HTTP. Registros de negócio criados nesse contexto precisam de `tenant_id` explícito. Novos usos dessas APIs devem ser revisados como operações globais.

## Permissões dentro do salão

Os papéis existentes são `admin`, `manager` e `professional`. `require_admin` e `require_manager` aceitam administrador e gerente; operações de proprietário, como cobrança e exportação completa, exigem `admin`.

Gerentes não podem criar ou alterar administradores. A alteração de usuários preserva pelo menos um administrador ativo e utiliza a trava compartilhada de mutações. Profissionais precisam de vínculo para acessar seus agendamentos e fotos; os endpoints de clientes aplicam o vínculo de atendimento correspondente. As permissões específicas permanecem nos routers e não substituem o escopo de salão.

## Fotos e auditoria

As fotos ficam em um diretório compartilhado configurado por `UPLOAD_DIR`, com nomes aleatórios. Não existem subpastas obrigatórias por salão. O nome do arquivo não é uma credencial.

`GET /uploads/{filename}` exige autenticação, valida o caminho e procura uma referência ao arquivo em um agendamento do salão atual. Para um profissional, também verifica o vínculo com o agendamento. A resposta utiliza `Cache-Control: private, no-store`.

O upload aceita JPEG, PNG e WebP identificados por assinatura de bytes, até 5 MiB por imagem. A conclusão de um atendimento só aceita referências de fotos já ligadas a ele; não permite apropriar-se de uma foto de outra conta passando sua URL. A validação não é um serviço de antivírus nem uma análise completa do conteúdo da imagem.

[audit.py](audit.py) registra mutações HTTP com identidade efetivamente autenticada, salão, método, caminho, status e IP. Tentativas anônimas permanecem no log estruturado de requisições. A trilha não grava corpos ou tokens e não constitui um histórico completo de todas as alterações feitas diretamente no banco.

## Jobs e concorrência

Aniversários e lembretes usam sessões explícitas de sistema e consultam salões com `is_active=true`. Esses jobs não dependem do bloqueio HTTP por assinatura: um salão com cobrança vencida e ainda ativo pode continuar recebendo esse processamento.

O agendador utiliza o horário do servidor; não existe configuração por salão. Os lembretes usam a janela de 24 a 25 horas antes do atendimento. O aniversário tem uma verificação de concessão anterior no mês.

[domain_locks.py](domain_locks.py) coordena as mutações que compartilham saldos e estados, como conclusão de atendimento, bônus de aniversário, estoque e alterações de administradores. Em produção, [runtime_guard.py](runtime_guard.py) mantém uma trava de sessão PostgreSQL que impede uma segunda API no mesmo banco. Isso sustenta a implantação de um único processo; não implementa escalabilidade horizontal.

Limites de requisições e travas de negócio continuam em memória. SMTP não possui uma fila durável de entrega. Replicação da API, filas distribuídas ou maior tolerância a falhas exigem trabalho adicional antes de mudar esse modelo operacional.

## Migração de instalações existentes

A migração [d9e64a3b2f10](migrations/versions/d9e64a3b2f10_saas_tenant_isolation.py):

1. Detecta colisões de e-mail após remoção de espaços externos e conversão para minúsculas. Se encontrar colisões, interrompe antes da alteração de schema para permitir a correção dos cadastros.
2. Normaliza os e-mails existentes.
3. Cria o salão `legacy`, ID 1, e vincula os dados anteriores a ele.
4. Acrescenta os campos, índices e constraints de isolamento, além dos registros de recuperação de senha e eventos de cobrança.
5. Inicia o salão legado com teste de 14 dias contado da migração e ajusta a sequência de IDs do PostgreSQL.

Os JWTs antigos, sem os campos novos, deixam de ser aceitos. É necessário entrar novamente. A migração não possui downgrade automático: reverter requer restaurar um backup anterior verificado, pois juntar dados de salões distintos destruiria a separação.

`bootstrap_admin.py` permite criar um administrador por acesso ao host. `seed.py` cria dados fictícios no salão `demo` e é permitido somente em `APP_ENV=development`.

## Operação da plataforma e limites atuais

[platform_admin.py](platform_admin.py) permite listar, suspender e restaurar salões por acesso ao host. Suspender/restaurar exige ID, confirmação do slug e motivo; registra auditoria e revoga sessões. Essas ações não alteram a assinatura no Stripe. Não há papel `platform_admin` nem painel de suporte global exposto por HTTP.

Também não estão implementados: múltiplos salões por usuário, domínios próprios por conta, RLS, quotas comerciais por salão, exclusão automática de contas ou arquivos órfãos, residência regional de dados e isolamento físico por cliente. Backups do banco e das fotos são operações da instalação inteira; a exportação individual é descrita no documento de cobrança.

## Verificação e manutenção

Os testes relevantes estão em:

- [test_tenancy.py](tests/test_tenancy.py): isolamento HTTP, JWT, referências e fotos.
- [tenancy_helpers.py](tests/tenancy_helpers.py): consultas, agregados, aliases, relacionamentos, operações em lote e constraints do banco.
- [test_postgres_tenancy.py](tests/test_postgres_tenancy.py): as mesmas verificações contra PostgreSQL migrado; exige `TEST_POSTGRES_URL` e é ignorado quando essa variável não está definida.
- [test_tenant_migration.py](tests/test_tenant_migration.py): migração e normalização dos e-mails legados.
- [test_concurrent_mutations.py](tests/test_concurrent_mutations.py): saldos compartilhados e preservação de administrador ativo.

A [configuração de CI](.github/workflows/ci.yml) contém execução de testes, verificação de migrações e restauração em PostgreSQL. Consulte o resultado da execução referente ao commit implantado; a presença do workflow, isoladamente, não comprova que uma implantação está saudável.
