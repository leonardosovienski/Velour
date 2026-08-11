# Operação do MVP em produção

## Pré-requisitos

- Docker com Compose
- domínio e proxy HTTPS na frente da porta 8080
- local externo para cópias de segurança

## Primeira inicialização

1. Copie `.env.example` para `.env`.
2. Configure `POSTGRES_PASSWORD`, uma `SECRET_KEY` aleatória com ao menos 32 caracteres e `CORS_ORIGINS` com o domínio HTTPS real.
3. (Opcional) Configure `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM` para habilitar e-mail de confirmação de agendamento e lembrete 24h antes. Sem SMTP configurado, a aplicação funciona normalmente e apenas pula o envio (logado como INFO).
4. Execute `docker compose up -d --build`.
5. Crie o primeiro administrador sem usar o seed de demonstração:

   ```bash
   docker compose exec api python bootstrap_admin.py
   ```

O container da API executa `alembic upgrade head` antes de iniciar. Em produção, nunca execute `seed.py`.

## Migrações

Antes de publicar uma nova versão:

```bash
docker compose run --rm api alembic upgrade head
```

Faça backup antes de qualquer migração. Downgrades devem ser testados e usados apenas como parte de um rollback planejado.

## Backup mínimo

Banco:

```bash
docker compose exec -T db pg_dump -U velour -d velour -Fc > velour.dump
```

As fotos ficam no volume `uploads_data`. Banco e fotos devem ser copiados diariamente para armazenamento externo criptografado, com retenção definida. Teste a restauração mensalmente; um backup nunca restaurado ainda não é uma garantia.

## Verificações após deploy

- `GET /api/health` responde 200 e informa `production`.
- login do administrador funciona;
- criação de cliente e agendamento funcionam;
- upload e leitura autenticada de foto funcionam;
- fechamento de atendimento (`/complete`) registra pagamento corretamente (`paid`, `amount_paid`, `payment_method`);
- se SMTP configurado, o e-mail de confirmação chega ao criar um agendamento de teste;
- logs (stdout, JSON estruturado) não contêm senha, token ou dados pessoais desnecessários.

## Jobs agendados

Dois jobs rodam in-process via APScheduler dentro do próprio container da API — não são serviços separados:

- `birthday_scheduler.py` — 08h00, concede pontos de aniversário.
- `reminder_scheduler.py` — de hora em hora, envia lembrete por e-mail para agendamentos ~24h à frente (idempotente via `reminder_sent`).

Ambos assumem uma única réplica da API. Rodar múltiplas réplicas/workers duplicaria a execução dos jobs (lembretes/pontos de aniversário em duplicidade) — não fazer isso sem introduzir um lock distribuído (Redis) ou mover os jobs para um worker dedicado.

## Permissões e auditoria

- `admin` e `manager` acessam administração, relatórios, fidelidade global, indicações e custos de estoque.
- `professional` precisa estar vinculado a exatamente um cadastro de profissional e fica limitado à própria agenda, aos próprios indicadores e aos clientes com quem já possui agendamento.
- Toda requisição `POST`, `PUT`, `PATCH` ou `DELETE` gera um registro em `/audit-logs`, consultável apenas por admin/manager. A trilha guarda usuário, método, caminho, status, IP e horário; corpos, senhas e tokens não são persistidos.
- Após atualizar uma base que já possua usuários com papel `professional`, vincule cada usuário ao cadastro correto antes de reativar o acesso. A migração mantém o campo inicialmente anulável para não interromper dados existentes, mas a API bloqueia profissionais sem vínculo.

Valores monetários usam `NUMERIC` no banco e `Decimal` nas regras de negócio. Isso inclui preços, receita acumulada, descontos, metas, comissões e custo unitário; quantidades físicas de estoque continuam permitindo casas decimais como medidas, não como dinheiro.

## Limites desta base

O Compose é adequado para desenvolvimento e primeiro piloto gerenciado. HTTPS, backups externos, armazenamento de objetos, alta disponibilidade e isolamento multi-tenant dependem da infraestrutura escolhida e ainda precisam ser configurados para a operação comercial. A aplicação já emite logs estruturados em JSON (stdout) prontos para qualquer coletor (CloudWatch, Loki, journald etc.), mas nenhum coletor/alerta está configurado nesta base — isso também depende da infraestrutura escolhida.
