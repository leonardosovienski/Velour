# Fiscal — MVP para demonstração

## Implementado

O módulo **Fiscal** demonstra os serviços do salão para clientes e as assinaturas do Velour para salões. Todo documento contém **DEMONSTRAÇÃO — SEM VALIDADE FISCAL**.

- Cadastro fiscal do prestador, CPF/CNPJ numérico validado, endereço, inscrição municipal, regime, código de serviço e alíquota ilustrativa.
- Rascunho de atendimento concluído com valor calculado no servidor; rascunho de assinatura com referência única e valor informado pelo operador.
- Emissão simulada com identificador `DEMO-...`, consulta, cancelamento com motivo e histórico.
- Dados de prestador/tomador preservados no documento; mudanças no cadastro não alteram o histórico.
- Uma origem por documento; repetir emissão/cancelamento não duplica efeitos. Cancelamento não libera reemissão da mesma origem neste MVP.
- Download autenticado de demonstrativo HTML sem scripts; pode ser impresso ou salvo em PDF pelo navegador.
- Documentos recebidos do Velour visíveis apenas no salão destinatário, sem permissão para emitir/cancelar em nome do Velour.
- Exportação inclui os registros fiscais. Consulta/download permanecem disponíveis após vencimento da assinatura.

**Limites:** não há emissão real, certificado, XML fiscal, protocolo, conexão com Receita/prefeitura, apuração tributária, retenções, IBS/CBS, substituição nem emissão automática por Stripe. O ISS é apenas `valor × alíquota / 100`, com Decimal e arredondamento HALF_UP. O resultado não representa tributo devido. CNPJ alfanumérico não é suportado neste MVP. Assinaturas demonstrativas são lançamentos manuais e não comprovam pagamento.

## Ativar

Instale dependências, execute `python -m alembic upgrade head` e configure no servidor:

```dotenv
FISCAL_MODE=demo
FISCAL_DEMO_PLATFORM_USER_ID=1
```

O modo padrão é `disabled`: bloqueia novas operações, preservando leitura. O ID padrão é `0` (nenhum operador). **FISCAL_DEMO_PLATFORM_USER_ID só pode ser usado em development/test e é rejeitado em production.** O usuário deve ser administrador. Não há promoção automática de administradores de salão para operadores globais.

O administrador abre **Financeiro → Documentos fiscais** pelo menu. Gerentes/profissionais não acessam os dados fiscais. Para o operador explicitamente configurado aparece um link separado **Administração Velour**, que abre a emissão para assinantes. **Financeiro → Assinatura Velour** contém o plano e os documentos recebidos pelo salão conectado. Consulte [FINANCEIRO_MVP.md](FINANCEIRO_MVP.md).

## Dados fictícios para apresentação

Em um ambiente virtual instalado, no PowerShell, use um banco **novo e descartável**:

```powershell
$env:APP_ENV = 'development'
$env:SECRET_KEY = python -c 'import secrets; print(secrets.token_hex(32))'
$env:DATABASE_URL = 'sqlite:///./fiscal-demo.db'
$env:AUTO_CREATE_TABLES = 'false'
$env:SCHEDULER_ENABLED = 'false'
$env:FISCAL_MODE = 'demo'
python -m alembic upgrade head
python demo_fiscal.py
```

O script recusa bancos com dados existentes; permite apenas o salão vazio de compatibilidade criado pela migração, que permanece intacto. Não apaga nem reinicializa bancos. Cria conta, salão, quatro atendimentos e exemplos de rascunho/emissão/cancelamento/assinatura. Exibe senha aleatória de demonstração e o ID do operador.

No mesmo terminal, use o ID informado:

```powershell
$env:FISCAL_DEMO_PLATFORM_USER_ID = '1'
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Em outro terminal, no diretório `frontend`: `npm ci` e `npm run dev -- --host 127.0.0.1`. Entre com as credenciais geradas e abra **Fiscal**.

### Roteiro

1. Mostrar o aviso de demonstração e o cadastro preenchido.
2. Consultar documento emitido, valores ilustrativos e histórico; baixar o demonstrativo.
3. Criar rascunho para o atendimento restante, preencher tomador e emitir demonstração.
4. Cancelar com motivo e conferir que o histórico permanece.
5. Na aba **Velour → assinantes**, criar documento com referência inédita, emitir e conferir em **Notas recebidas do Velour**.

Use somente dados fictícios. Códigos de serviço e alíquotas dos exemplos não são enquadramentos fiscais validados.

## API

- GET `/fiscal/config`: modo e capacidade de operação demonstrativa global.
- GET/PUT `/fiscal/profile`: cadastro do próprio salão.
- GET `/fiscal/appointments`: últimos 200 atendimentos concluídos elegíveis, sem documento.
- GET `/fiscal/documents?kind=salon` ou `kind=platform`: emitidos ou recebidos; `offset` e `limit` (1–200).
- POST `/fiscal/documents`: rascunho de atendimento; requer assinatura ativa.
- GET `/fiscal/documents/{id}`: documento no escopo do salão.
- POST `/fiscal/documents/{id}/simulate`: emissão simulada; requer assinatura ativa.
- POST `/fiscal/documents/{id}/cancel`: motivo de 15–300 caracteres.
- GET `/fiscal/documents/{id}/events` e `/print`: histórico e demonstrativo.
- `/fiscal-platform/profile`, `/tenants`, `/documents` e ações `/simulate`, `/cancel`, `/events`, `/print`: operador configurado, fora de produção; apenas documentos de assinatura.

Nenhum dado é enviado a serviço fiscal externo. Não há upload nem armazenamento de certificados/senhas fiscais.

## Integração direta futura em Araucária/PR

O MVP não utiliza provedor pago. A futura integração deve selecionar o emissor municipal ou nacional conforme as regras aplicáveis a cada emitente, implementar assinatura/validação de XML, credenciais por emitente, envio, reconciliação após timeout, autorização, cancelamento real e armazenamento de XML/DANFSe. Não basta trocar o estado `simulated` por `authorized`.

Referências consultadas em 15/09/2026:

- [Prefeitura de Araucária](https://araucaria.atende.net/cidadao/pagina/nfse-nota-fiscal-de-servicos-eletronica).
- [Documentação e esquemas oficiais do padrão nacional](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual).
- [Endereços oficiais dos ambientes](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao).

Esses conectores e a homologação real não fazem parte da entrega demonstrativa.
