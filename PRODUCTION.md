# Velour SaaS — implantação e operação

Esta versão implementa isolamento por salão, cadastro de administrador com 14 dias de teste, recuperação de senha, Stripe Checkout/Portal, webhooks assinados, exportação e bloqueio por assinatura. A liberação comercial depende da configuração e da validação no ambiente real descritas abaixo. Não há afirmação de auditoria externa, SLA ou conformidade jurídica automática.

## Arquitetura suportada

- Uma instância da API, **um worker**, PostgreSQL 17 e volume persistente de fotos.
- O PostgreSQL mantém um lock exclusivo durante a vida da API. Uma segunda instância é recusada para preservar os locks, limites de requisição e jobs locais.
- Caddy termina HTTPS; Nginx serve a SPA e encaminha `/api` à API. Somente 80/443 são públicas. 8080 fica em loopback; banco/API não publicam portas.
- A rede Docker `172.31.252.0/28` é reservada por esta instalação. Se conflitar com sua rede, altere **juntos** Compose, `frontend/nginx.conf` e a lista de proxies confiáveis do Uvicorn. Não confie em qualquer IP.
- A implantação usa uma migração separada, concluída antes da API. O container da API executa como usuário sem privilégios.
- Não há alta disponibilidade, failover ou escala horizontal nesta versão. Redis/fila distribuída seriam necessários para remover esta restrição.

## Configuração inicial

1. Em uma VM com Docker Compose, clone a versão revisada e copie `.env.example` para `.env`. Restrinja a leitura do arquivo ao operador.
2. Configure `APP_ENV=production`, `AUTO_CREATE_TABLES=false`, `APP_URL=https://seu-dominio`, `CORS_ORIGINS` igual a essa origem, `DOMAIN` sem protocolo e `ACME_EMAIL`.
3. Gere **dois segredos diferentes** com `python -c "import secrets; print(secrets.token_hex(32))"`: um para `SECRET_KEY`, outro para `POSTGRES_PASSWORD`. O Compose constrói a URL do banco; use senha hexadecimal para evitar caracteres reservados de URL.
4. Configure SMTP com STARTTLS (normalmente porta 587), remetente verificado, SPF/DKIM/DMARC no provedor. Teste uma recuperação de senha real. As credenciais nunca entram no frontend.
5. Publique Termos de Uso e Política de Privacidade com os dados reais da sua empresa. Os arquivos Markdown no repositório continuam sendo rascunhos. Configure `TERMS_URL`, `PRIVACY_URL`, `TERMS_VERSION`; mantenha `SIGNUP_ENABLED=false` até a publicação e a validação do ambiente.
6. Configure Stripe conforme a seção seguinte. A mensalidade vem do Price do Stripe; nenhum preço de venda foi arbitrariamente definido no código.
7. Aponte DNS do domínio para a VM e libere 80/443. Execute:

```sh
docker compose -f compose.yaml -f compose.production.yaml up -d --build
```

Caddy solicita e renova o certificado quando DNS e portas estão corretos. O banco e as fotos usam volumes persistentes. Não execute `seed.py` em produção. O primeiro salão comercial se cadastra em `/signup` depois da liberação; `bootstrap_admin.py` serve para operação assistida de um salão legado.

## Stripe: homologação e ativação

- Crie um produto e um **Price recorrente mensal**, quantidade 1, no Dashboard do Stripe. Configure `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`.
- Comece em sandbox: `STRIPE_LIVEMODE=false`. Não misture IDs/chaves/eventos de sandbox e produção.
- Configure o destino `https://seu-dominio/api/billing/webhook`, com os eventos: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `customer.subscription.paused`, `customer.subscription.resumed`, `invoice.paid`, `invoice.payment_succeeded`, `invoice.payment_failed`, `invoice.payment_action_required`.
- Habilite o Customer Portal com atualização de pagamento e cancelamento. Desabilite mudança para preços que a aplicação não suporta.
- A confirmação no navegador nunca ativa a conta. O webhook assinado lê a assinatura atual no Stripe e persiste o resultado. Eventos repetidos não reaplicam processamento. Falhas transitórias respondem erro para o Stripe tentar novamente.
- Cadastros têm 14 dias de teste sem cartão. Checkout durante o teste conserva o fim do período; perto do vencimento pode estender até 49 horas a partir do Checkout por exigência do gateway, sem antecipar cobrança. O Checkout mostra o valor/data.
- `past_due` tem até 7 dias de carência desde a fatura não paga. Teste vencido, cancelamento e estados sem direito de acesso bloqueiam rotas de negócio com 402. Login, cobrança, exportação e leitura autorizada de fotos continuam disponíveis enquanto a conta não estiver suspensa.
- Depois dos testes, configure o Price, webhook e chaves **de produção**, `STRIPE_LIVEMODE=true`, abra cadastros e execute a verificação abaixo. Validar cobrança real exige sua conta e sua autorização para uma compra de teste.

Referências: [Stripe webhooks](https://docs.stripe.com/webhooks), [Checkout](https://docs.stripe.com/api/checkout/sessions/create), [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy), [ordem de inicialização do Compose](https://docs.docker.com/compose/how-tos/startup-order/).

## Verificação de liberação

```sh
docker compose exec api python preflight.py --strict --services
```

O comando é somente leitura: verifica configuração, versão do banco e Price no Stripe; nunca imprime chaves nem cria cobranças. Resultado positivo **não substitui** estes testes reais:

- Abra duas contas de salões. Cadastre cliente, profissional, serviço, agendamento e foto em uma. A outra não deve listar nem acessar por ID os recursos da primeira.
- Conclua atendimento e valide pagamento, estoque, pontos e relatórios. Confira o fuso horário do host/container: os horários operacionais são locais, sem conversão por salão.
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

O script pausa a API, cria um dump PostgreSQL e um arquivo das fotos, registra hashes SHA-256 e reinicia a API mesmo se o backup falhar. Só existe `manifest.json` em backups concluídos. O script não exclui backups antigos. Copie banco, fotos e manifesto para **armazenamento externo criptografado**; defina retenção, acesso e frequência conforme o contrato. Guarde a configuração de produção separadamente e com proteção adequada.

Para ensaiar restauração, use uma VM/Compose separado, um banco vazio e volumes novos. Confira os hashes do manifesto, restaure com `pg_restore --exit-on-error` e extraia as fotos em `/data/uploads` preservando acesso do usuário `velour`. Execute migrações e repita login, consulta e leitura de fotos. Nunca teste restauração sobre o banco comercial. A CI restaura um dump em um segundo banco PostgreSQL descartável; isso não valida suas cópias externas.

## Atualizações, dados existentes e rollback

1. Faça backup consistente e anote a versão em execução.
2. Pare a API antes de migrar: `docker compose stop api`.
3. Atualize o código/imagens e rode `docker compose run --rm migrate`.
4. Suba os serviços e execute preflight + smoke tests.
5. Se necessário, restaure o snapshot em ambiente separado e retorne a versão compatível. O downgrade da migração de multi-tenancy é intencionalmente recusado para preservar o isolamento e os dados. Use a restauração do snapshot verificado para rollback.

A migração atribui os dados anteriores ao salão legado (id 1), sem misturar cadastros novos. Sessões antigas não contêm tenant/token_version e exigem novo login. Verifique e-mails duplicados por maiúsculas/minúsculas antes de migrar. O e-mail de usuário permanece único na plataforma; uma conta não participa de vários salões.

## Suporte e privacidade

O administrador do salão exporta os dados na tela Assinatura. O JSON exclui hashes de senha, tokens de recuperação e segredos; fotos são referências para download autenticado. Suspensão, atendimento de solicitações de exclusão/anonimização e retenção de backups continuam sendo processos do operador: a exclusão normal de um cadastro é **desativação lógica**, não apagamento definitivo. Não prometa eliminação automática nem prazo de retenção que não esteja operacionalizado. Não há painel global de suporte nem emissão fiscal automática nesta versão.

### Operação assistida de contas

Use `docker compose exec api python platform_admin.py list` para consultar salões sem expor e-mails ou credenciais. Para suspender/reativar uma conta, use `suspend` ou `resume`, o ID e os argumentos obrigatórios `--confirm-slug` e `--reason`. A ação fica em auditoria e invalida sessões anteriores; não concede assinatura nem altera cobranças. Execute apenas por operadores autorizados com acesso ao host. Não existe função pública para elevar um usuário a administrador da plataforma.
