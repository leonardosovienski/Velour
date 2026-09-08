# Velour SaaS — implantação e operação

Esta versão implementa isolamento por salão, cadastro de administrador com 14 dias de teste, recuperação de senha, Stripe Checkout/Portal, webhooks assinados, exportação e bloqueio por assinatura. Este guia descreve uma implantação em VM Linux com Docker Engine, plugin Docker Compose e Python 3.11 ou superior no host para backups. A liberação comercial depende da configuração e da validação do ambiente real descritas abaixo.

## Arquitetura suportada

- Uma instância da API, **um worker**, PostgreSQL 17 e volume persistente de fotos.
- O PostgreSQL mantém um lock exclusivo durante a vida da API. Uma segunda instância é recusada para preservar os locks, limites de requisição e jobs locais.
- Caddy termina HTTPS; Nginx serve a SPA e encaminha `/api` à API. Somente 80/443 são públicas. 8080 fica em loopback; banco/API não publicam portas.
- A rede Docker `172.31.252.0/28` é reservada por esta instalação. Se conflitar com sua rede, altere **juntos** Compose, `frontend/nginx.conf` e a lista de proxies confiáveis do Uvicorn. Não confie em qualquer IP.
- A implantação usa uma migração separada, concluída antes da API. O container da API executa como usuário sem privilégios.
- Todos os salões usam um único fuso operacional. Configure `SALON_TIMEZONE` com um identificador IANA, por exemplo `America/Sao_Paulo`; os horários de atendimento são locais. A imagem contém a base de fusos `tzdata`.
- Não há alta disponibilidade, failover ou escala horizontal nesta versão. Escalar exige redesenhar locks, rate limits e agendamento de jobs para coordenação compartilhada.

## Configuração inicial

### Separar os testes da operação comercial

Em 8 de setembro de 2026, o responsável pelo projeto confirmou que todos os agendamentos cadastrados até essa data são dados de teste. Esse histórico não precisa de correção de horário para a abertura comercial.

Inicie a operação comercial em uma instalação com banco e volume de fotos novos, separados da homologação. Execute as migrações e crie as contas comerciais; não importe o banco de testes nem execute `seed.py`. Assim, atendimentos fictícios e seus efeitos em estoque, fidelidade e relatórios não entram na operação real. Os dados de teste podem permanecer no ambiente de homologação. A partir da entrada em produção, aplique os procedimentos de backup e atualização deste guia aos dados reais.

### Preparar o ambiente

1. Em uma VM com os requisitos acima, clone a versão revisada. Na raiz do repositório, copie `.env.example` para `.env` somente na instalação inicial e restrinja sua leitura ao operador (`chmod 600 .env` no Linux). Não salve segredos no Git.
2. Configure `APP_ENV=production`, `AUTO_CREATE_TABLES=false`, `APP_URL=https://seu-dominio`, `CORS_ORIGINS` igual a essa origem, `DOMAIN` sem protocolo e `ACME_EMAIL`.
3. Gere **dois segredos diferentes** com `python -c "import secrets; print(secrets.token_hex(32))"`: um para `SECRET_KEY`, outro para `POSTGRES_PASSWORD`. O Compose constrói a URL do banco; use senha hexadecimal para evitar caracteres reservados de URL.
4. Configure SMTP com STARTTLS (normalmente porta 587), remetente verificado, SPF/DKIM/DMARC no provedor. Teste uma recuperação de senha real. As credenciais nunca entram no frontend.
5. Preencha e revise as minutas de [Termos de Uso](TERMOS_DE_USO.md) e [Política de Privacidade](POLITICA_DE_PRIVACIDADE.md) e publique páginas HTTPS com os dados reais da empresa. O frontend não publica esses Markdown automaticamente. Configure `TERMS_URL`, `PRIVACY_URL` e uma `TERMS_VERSION` identificável; mantenha `SIGNUP_ENABLED=false` até a publicação e a validação do ambiente.
6. Configure Stripe conforme a seção seguinte. A mensalidade vem do Price do Stripe; nenhum preço de venda foi arbitrariamente definido no código.
7. Aponte DNS do domínio para a VM e libere 80/443. Execute:

```sh
docker compose -f compose.yaml -f compose.production.yaml up -d --build
```

Caddy solicita e renova o certificado quando DNS e portas estão corretos. O banco e as fotos usam volumes persistentes. Não execute `seed.py` em produção. O primeiro salão comercial se cadastra em `/signup` depois da liberação; `docker compose exec api python bootstrap_admin.py` permite criar um administrador de forma assistida em um salão novo ou existente. Não há credenciais padrão; o bootstrap deve ser executado somente por operador autorizado.

O Compose define `DATABASE_URL` para o PostgreSQL interno, `APP_ENV=production`, `AUTO_CREATE_TABLES=false` e scheduler ativo, sobrescrevendo esses valores do arquivo. Não execute Alembic, bootstrap ou preflight diretamente no host usando o `DATABASE_URL` SQLite do exemplo. Os comandos `exec` deste guia usam os mesmos containers criados na raiz do repositório; o arquivo base basta para essas operações. Subir, reconstruir ou recriar serviços públicos requer também o overlay de produção.

Não altere o nome do projeto Compose entre comandos. O script de backup usa o projeto derivado desta pasta e o arquivo base `compose.yaml`; se sua operação adotar um nome próprio, mantenha `COMPOSE_PROJECT_NAME` consistente em todas as execuções e valide a seleção dos serviços antes de agendar backups.

## Stripe: homologação e ativação

- Crie um produto e um **Price recorrente mensal**, quantidade 1, no Dashboard do Stripe. Configure `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`.
- Comece em sandbox: `STRIPE_LIVEMODE=false`. Não misture IDs/chaves/eventos de sandbox e produção.
- Configure o destino `https://seu-dominio/api/billing/webhook`, com os eventos: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `customer.subscription.paused`, `customer.subscription.resumed`, `invoice.paid`, `invoice.payment_succeeded`, `invoice.payment_failed`, `invoice.payment_action_required`.
- Habilite o Customer Portal com atualização de pagamento e cancelamento. Desabilite mudança para preços que a aplicação não suporta.
- A confirmação no navegador nunca ativa a conta. O webhook assinado lê a assinatura atual no Stripe e persiste o resultado. Eventos repetidos não reaplicam processamento. Falhas transitórias respondem erro para o Stripe tentar novamente.
- Cadastros têm 14 dias de teste sem cartão. Checkout durante o teste conserva o fim do período; perto do vencimento pode estender até 49 horas a partir do Checkout por exigência do gateway, sem antecipar cobrança. O Checkout mostra o valor/data.
- `past_due` tem até 7 dias de carência desde a fatura não paga. Teste vencido, cancelamento e estados sem direito de acesso bloqueiam rotas de negócio com 402. Login, cobrança, exportação e leitura autorizada de fotos continuam disponíveis enquanto a conta não estiver suspensa.
- Depois dos testes em sandbox, configure o Price, webhook e chaves **de produção**, `STRIPE_LIVEMODE=true` e `SIGNUP_ENABLED=true`. Recrie a API com `docker compose -f compose.yaml -f compose.production.yaml up -d --build` para carregar a configuração e execute a verificação abaixo. Registre a evidência da validação comercial feita pelo responsável pela conta Stripe; testes automatizados não realizam uma compra real.

Referências técnicas: [Stripe webhooks](https://docs.stripe.com/webhooks), [Checkout](https://docs.stripe.com/api/checkout/sessions/create), [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy), [ordem de inicialização do Compose](https://docs.docker.com/compose/how-tos/startup-order/).

## Verificação de liberação

```sh
docker compose exec api python preflight.py --strict --services
```

O comando é somente leitura: verifica configuração, versão do banco e existência de salões, além de consultar o Price no Stripe. `--strict` exige cadastro público habilitado e modo de cobrança real; para validar sandbox com cadastro ainda fechado, use apenas `--services`. Ele não imprime chaves nem cria cobranças. A checagem de documentos/SMTP confirma configuração, não a publicação das páginas nem a entrega de mensagens. Resultado positivo **não substitui** estes testes reais:

- Abra duas contas de salões. Cadastre cliente, profissional, serviço, agendamento e foto em uma. A outra não deve listar nem acessar por ID os recursos da primeira.
- Conclua atendimento normal e cortesia de R$ 0; valide valores, comissão, estoque, pontos e relatórios. Confira o fuso do container e a hora mostrada na agenda.
- Teste login em navegador novo, recuperação de senha entregue, link expirado/reutilizado e invalidação da sessão antiga.
- Teste checkout sandbox, renovação, falha de pagamento, regularização, cancelamento, webhook repetido e indisponibilidade do gateway. Confira no Dashboard as entregas dos eventos.
- Teste vencimento do trial, acesso à tela Assinatura, exportação e imagens protegidas sem assinatura ativa.
- Teste celular e navegação de administrador, gerente e profissional. Faça um piloto com dados de teste antes de aceitar clientes pagantes.
- Configure monitoramento externo de `/api/health` a cada minuto, alertas de falha, espaço em disco, backup e erros de webhook/SMTP. Os logs JSON no stdout não substituem um alerta configurado.

## Backup e restauração

Execute diariamente no host, em uma janela de manutenção:

```sh
python scripts/backup.py --directory /diretorio-seguro/backups
```

O script pausa a API, cria um dump PostgreSQL e um arquivo das fotos e registra hashes SHA-256. Ao sair da etapa de cópia, tenta reiniciar a API, inclusive em caso de falha. `manifest.json` identifica a conclusão dos arquivos do backup; confirme também o código de saída e a saúde da API após o reinício. Uma pasta sem manifesto pode conter apenas arquivos parciais.

O script restringe permissões dos arquivos no host, mas não agenda execuções, cifra os dados, exclui cópias antigas nem transfere arquivos para outro servidor. Copie banco, fotos e manifesto para **armazenamento externo criptografado** e configure alerta para falha/ausência de backup. Defina retenção, acesso e frequência conforme o contrato. Guarde a configuração de produção separadamente e com proteção adequada; o backup contém dados pessoais e hashes de senha.

Para ensaiar restauração, use uma VM separada e um projeto Compose sem volumes anteriores:

1. Recupere uma cópia externa e a revisão do código compatível. Mantenha SMTP e integrações reais desabilitados no ensaio.
2. Compare os SHA-256 de `database.dump` e `uploads.tar.gz` com `manifest.json`. Não prossiga com arquivos ausentes ou diferentes.
3. Inicie somente um PostgreSQL vazio: `docker compose up -d db`. Restaure o dump com `pg_restore --exit-on-error` nesse banco, usando o usuário `velour`. Não inicie a migração antes da restauração, para evitar tabelas já existentes.
4. Extraia `uploads.tar.gz` no volume novo montado em `/data/uploads`, preservando o acesso do usuário `velour` da imagem. Não extraia o arquivo sobre fotos de outro ambiente.
5. Suba a revisão compatível do serviço, execute preflight e repita login, consulta e leitura de fotos. Registre duração, data do backup e resultado para definir objetivos reais de recuperação.

Nunca teste restauração sobre o banco comercial. A CI restaura um dump em um segundo banco PostgreSQL descartável; isso não valida suas cópias externas, fotos ou tempo de recuperação do ambiente real.

## Atualizações, dados existentes e rollback

1. Faça backup consistente, verifique sua cópia externa e anote a revisão em execução. O backup reinicia a API; planeje a parada da etapa seguinte.
2. Pare a API antes de migrar: `docker compose stop api`.
3. Atualize o checkout para a revisão aprovada. Reconstrua as imagens antes de usar o migrador: `docker compose -f compose.yaml -f compose.production.yaml build`.
4. Execute `docker compose run --rm migrate` e confira o código de saída. Se falhar, mantenha a API parada e investigue antes de continuar.
5. Execute `docker compose -f compose.yaml -f compose.production.yaml up -d`, confirme `/api/health`, rode preflight e os testes essenciais de login, agenda e cobrança.
6. Se necessário, restaure o snapshot em ambiente separado e retorne à revisão compatível. O downgrade da migração de multi-tenancy é intencionalmente recusado para preservar o isolamento e os dados. Use o snapshot verificado para rollback; não force downgrade nem apague volumes para corrigir uma atualização.

A migração atribui os dados anteriores ao salão legado (id 1), sem misturar cadastros novos. Sessões antigas não contêm tenant/token_version e exigem novo login. Verifique e-mails duplicados por maiúsculas/minúsculas antes de migrar. O e-mail de usuário permanece único na plataforma; uma conta não participa de vários salões.

A agenda recebe horários locais sem `Z` ou offset; a interface conserva o horário digitado. Versões anteriores convertiam esse campo para UTC antes de enviá-lo ao banco sem fuso. Se uma instalação dessas versões contiver agendamentos reais, confira seus horários antes de migrá-los: a origem e o fuso usados em cada cadastro antigo não estão registrados. Essa conferência não é necessária para os agendamentos de teste do projeto que ficarão no ambiente de homologação.

## Suporte e privacidade

O administrador do salão exporta os dados na tela Assinatura. O JSON exclui hashes de senha, tokens de recuperação e segredos; fotos são referências para download autenticado. Suspensão, atendimento de solicitações de exclusão/anonimização e retenção de backups continuam sendo processos do operador. Clientes, profissionais e usuários são desativados preservando histórico; outros recursos têm regras próprias de exclusão. Essas ações não constituem um processo completo de eliminação de dados pessoais. Não há painel global de suporte nem emissão fiscal automática nesta versão.

### Operação assistida de contas

Use `docker compose exec api python platform_admin.py list` para consultar salões sem expor e-mails ou credenciais. Para suspender/reativar uma conta, use `suspend` ou `resume`, o ID e os argumentos obrigatórios `--confirm-slug` e `--reason`. A ação fica em auditoria e invalida sessões anteriores; não concede assinatura nem altera cobranças. Execute apenas por operadores autorizados com acesso ao host. Não existe função pública para elevar um usuário a administrador da plataforma.
