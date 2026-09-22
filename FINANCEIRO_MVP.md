# Financeiro do Velour

O menu Financeiro reúne seis áreas em `/finance/overview`: Visão geral, Recebimentos, Despesas, Contábil, Documentos fiscais e Assinatura Velour. `/fiscal` encaminha para os documentos; `/billing` mantém compatibilidade com retornos do Stripe e onboarding dentro da nova estrutura.

## Regras

- Administradores e gerentes consultam os recebimentos dos atendimentos concluídos, registram quitação do saldo e cadastram despesas. Profissionais não acessam esses registros.
- O resumo agrupa atendimentos pelo mês do serviço e despesas pelo mês do vencimento. Não representa fluxo de caixa por data do pagamento, saldo bancário ou lucro contábil. Recebimentos parciais antigos são considerados pelo valor registrado; a nova ação quita o saldo integral.
- Registrar recebimento é uma anotação operacional: não cobra, não transfere dinheiro, não repete pontos/estoque e não emite documentos fiscais. Repetir a quitação não aumenta o valor recebido.
- Despesas têm descrição, categoria, valor, vencimento e data de pagamento opcional. O pagamento pode ser registrado depois, sem duplicar efeitos. Neste MVP não há parcelas, recorrência, anexos, edição ou exclusão de despesas, estornos ou conciliação bancária.
- Despesas persistem no banco e estão na exportação do salão. Não são simuladas em armazenamento local do navegador. A demonstração deve usar somente dados fictícios.
- Documentos fiscais continuam demonstrativos, sem validade fiscal; veja FISCAL_MVP.md. Links nos recebimentos abrem o documento existente ou preenchem o atendimento no rascunho.
- Plano e documentos recebidos do Velour ficam em Assinatura Velour. A emissão Velour → assinantes tem página separada `/platform/fiscal`, disponível apenas ao operador demonstrativo configurado, fora de produção.
- As rotas financeiras exigem assinatura ativa; consulta fiscal e cobrança mantêm as exceções existentes para contas vencidas.

## Contábil (demonstração acadêmica)

A área Contábil (`/finance/accounting`) monta, para o mês de referência, a DRE, o livro diário com lançamentos em partidas dobradas e o balancete de verificação, usando um plano de contas simplificado. Tudo é calculado na hora a partir dos registros existentes: não há tabela nova, escrituração oficial, SPED nem apuração de tributos. O relatório pode ser baixado em TXT ou PDF, sempre com o aviso de que não tem validade contábil ou fiscal.

- Receita e comissão (`commission_rate` do profissional) entram pela data do atendimento concluído; o recebimento registrado baixa Clientes a receber contra Caixa.
- Insumos consumidos são valorizados pelo `cost_per_unit` do produto na data do movimento de estoque. O relatório não registra compras, então a conta de estoque mostra apenas as saídas do mês.
- O ISS é estimado com a alíquota do cadastro fiscal demonstrativo; sem cadastro, a alíquota é zero.
- Despesas entram pelo vencimento e, quando pagas, baixam Contas a pagar contra Caixa.
- Administradores e gerentes acessam; profissionais recebem 403.

## Banco e apresentação

Execute `python -m alembic upgrade head` antes de iniciar a versão nova. A revisão `f2a3b4c5d6e7` acrescenta a tabela `expenses`; não altera os atendimentos ou documentos existentes.

Para um ambiente novo, siga a preparação de FISCAL_MVP.md. Abra Financeiro, consulte os recebimentos, registre uma despesa fictícia e confira o resumo do mês. Em Recebimentos, use Preparar documento para abrir os dados do atendimento; pagamento e emissão são ações independentes.

## API

- GET `/finance/overview?month=AAAA-MM`: resumo, recebimentos e despesas do mês.
- POST `/finance/expenses`: criação de despesa.
- POST `/finance/expenses/{id}/pay`: registro da data do pagamento.
- POST `/finance/receipts/{appointment_id}/settle`: registro de recebimento integral com forma de pagamento.
- GET `/accounting/report?month=AAAA-MM`: DRE, lançamentos, balancete e plano de contas do mês.
- GET `/accounting/report/download?month=AAAA-MM&format=txt|pdf`: mesmo relatório em arquivo.

As consultas usam o escopo autenticado do salão. As mutações são serializadas conforme a arquitetura de API única do projeto. O resumo lista todos os registros do mês; paginação e relatórios de grande volume são evoluções futuras.
