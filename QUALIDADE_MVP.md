# Revisão geral do Velour — 16/09/2026

## Resultado
MVP local revisado, com Financeiro reunindo visão geral, recebimentos, despesas, documentos fiscais e assinatura. Código alterado localmente na branch feature/fiscal-direct-20260915; nenhuma publicação no GitHub ou implantação comercial realizada.

## O que foi enxugado e corrigido
- Páginas carregadas sob demanda: JavaScript inicial passou de 531,57 kB para 324,62 kB (cerca de 39% menor, sem compressão; atual gzip 104,91 kB). As demais páginas são baixadas ao navegar.
- Reutilização do componente de recuperação de erro e mensagem de carregamento com nova tentativa. Falha de API não aparece como métricas zeradas nem deixa carregamento infinito.
- Paginação de clientes e agenda com ordenação estável; busca explicitamente limitada à página atual.
- Tratamento de falhas em ações e modais; ficha técnica não pode ser sobrescrita se a leitura falhar; briefing descarta resposta antiga de outro cliente.
- Relatórios protegidos para os perfis corretos; datas inválidas/invertidas retornam 422 em vez de erro interno.
- Financeiro evita consultas repetidas por atendimento, atualiza corretamente links para documentos e mostra filtros sem resultados.
- Ajustes responsivos e testes de frontend com um worker para reduzir pressão de memória.

## Validação executada
| Verificação | Resultado |
|---|---|
| Suíte backend SQLite | 203 aprovados; 6 de PostgreSQL separados |
| PostgreSQL 17.11 | 6 aprovados, isolamento entre salões e consultas reais |
| Migração PostgreSQL | upgrade até f2a3b4c5d6e7; alembic check sem divergências |
| Backup e restauração PostgreSQL | pg_dump/pg_restore em segundo banco descartável; revisão conferida |
| Frontend | 51 testes aprovados em 15 arquivos |
| ESLint, TypeScript, build Vite | aprovados |
| npm audit e pip-audit | nenhuma vulnerabilidade conhecida encontrada |
| git diff --check | aprovado |
| Navegador | login, dashboard, clientes, agenda, profissionais, serviços, estoque, fidelidade, indicações, relatórios, usuários e cinco áreas do Financeiro carregaram |
| Responsividade | Financeiro em 390 × 844; largura da página 390, sem extravasamento horizontal da página |

O teste de endpoints cobre 30 leituras de telas administrativas. As suítes também cobrem autenticação, regras de negócio, permissões, assinatura simulada, financeiro e fiscal. Percorrer telas não significa testar manualmente cada combinação de formulário ou dispositivo.

Uma primeira execução backend teve falha de subprocesso do Windows; outra execução frontend terminou com timeout do worker (43 testes passaram antes da interrupção). Os registros foram preservados. A execução final backend com o runtime Python base e a repetição isolada frontend passaram. O computador apresentou pressão severa de memória durante a revisão; não foram encerrados processos de outros projetos. Há avisos de depreciação/SQLAlchemy nos logs, sem falhas nas execuções finais.

O PostgreSQL portátil foi obtido pelo link oficial de binários Windows: https://www.postgresql.org/download/windows/ → https://www.enterprisedb.com/download-postgresql-binaries . Rodou somente em 127.0.0.1:55432, com dados descartáveis e sem serviço instalado. Foi encerrado após os testes.

## Limites reais
- Fiscal é demonstrativo, sem validade fiscal e sem transmissão à Receita/prefeitura. Abrange documentos do salão e da assinatura Velour.
- Stripe e SMTP têm implementação e testes locais, mas não foram homologados com contas/credenciais reais nesta revisão.
- Recebimentos/despesas registram controle operacional; não movimentam dinheiro. O resumo mensal segue mês do atendimento/vencimento, não saldo bancário ou fluxo por data de pagamento.
- Despesas são básicas: cadastro e baixa; não há edição/exclusão, recorrência, parcelamento ou conciliação bancária neste MVP.
- Busca de clientes/agenda é por página, não pesquisa global no banco.
- HTTPS, infraestrutura de produção, backup externo, monitoramento e homologação comercial continuam conforme PRODUCTION.md.
- Testes aprovados sustentam a revisão local; não equivalem a garantia de ausência de todo defeito ou certificação de produção.

## Entrega e acesso
O ZIP contém código-fonte e documentação, sem banco, credenciais, dependências instaladas ou artefatos de build. Reinstale usando os arquivos de dependências e siga README.md, FINANCEIRO_MVP.md e FISCAL_MVP.md.

A apresentação local foi verificada em http://127.0.0.1:5173/finance/overview, com API em 127.0.0.1:8000. Usa cópia isolada qa-presentation-20260916.db; o banco de apresentação anterior foi preservado. A disponibilidade dessa URL depende de os processos locais continuarem ativos. Credenciais fictícias permanecem no guia ACESSO-DEMO.md entregue anteriormente.
