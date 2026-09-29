# Matriz de alinhamento

A professora exige alinhamento total entre a documentação no Confluence, a gestão no Jira, o protótipo no Figma e o código. Esta matriz lista o que existe em cada frente em 29/09/2026 e o que não bate.

## Épicos, código e telas

Os épicos e histórias vêm do projeto `VEL` do Jira. Os caminhos de código e telas vêm do repositório.

| Épico no Jira | Backend | Frontend | Testes principais |
|---|---|---|---|
| VEL-10 EP01 Autenticação e Controle de Acesso | `routers/auth.py`, `routers/users.py`, `routers/account_recovery.py`, `auth.py` | `pages/Login.tsx`, `pages/Users.tsx`, `pages/PasswordRecovery.tsx` | `test_api_integration.py`, `test_professional_access.py`, `test_commercial_hardening.py` |
| VEL-14 EP02 Gestão de Clientes | `routers/clients.py` | `pages/Clients.tsx`, `pages/ClientProfile.tsx`, `components/BriefingDrawer.tsx` | `test_tenancy.py`, `test_professional_access.py` |
| VEL-16 EP03 Agenda e Atendimentos | `routers/appointments.py`, `reminder_scheduler.py` | `pages/Appointments.tsx` | `test_appointments.py`, `test_concurrent_mutations.py`, `test_reminder_scheduler.py` |
| VEL-17 EP04 Profissionais e Serviços | `routers/professionals.py`, `routers/services.py` | `pages/Professionals.tsx`, `pages/Services.tsx` | `test_professional_dashboard.py`, `test_category_and_schedule_contract.py` |
| VEL-18 EP05 Estoque e Ficha Técnica | `routers/products.py`, `models/stock_movement.py`, `models/service_recipe.py` | `pages/Inventory.tsx` | `test_stock.py` |
| VEL-19 EP06 Fidelidade e Indicações | `routers/loyalty.py`, `routers/referrals.py`, `birthday_scheduler.py` | `pages/Loyalty.tsx`, `pages/Referrals.tsx` | `test_loyalty.py`, `test_tiers.py`, `test_tier_discount.py`, `test_referrals.py` |
| VEL-20 EP07 Dashboard e Relatórios | `routers/dashboard.py`, `routers/reports.py` | `pages/Dashboard.tsx`, `pages/Reports.tsx` | `test_dashboard_alerts.py`, `test_report_period_validation.py` |
| VEL-21 EP08 SaaS: Multi-salão e Assinatura | `routers/tenants.py`, `routers/billing.py`, `database.py` | `pages/Signup.tsx`, `pages/Billing.tsx` | `test_tenancy.py`, `test_saas.py`, `test_postgres_tenancy.py` |
| VEL-22 EP09 Módulo Financeiro | `routers/finance.py` | `pages/Finance.tsx` | `test_finance.py`, `test_financial_regressions.py` |
| VEL-23 EP10 Módulo Fiscal (demonstração) | `routers/fiscal.py`, `demo_fiscal.py` | `pages/Fiscal.tsx` | `test_fiscal.py`, `test_fiscal_demo_seed.py` |
| VEL-24 EP11 Módulo Contábil (demonstração) | `routers/accounting.py` | `pages/Accounting.tsx` | `test_accounting.py` |
| VEL-25 EP12 Entregas Acadêmicas | não se aplica | não se aplica | não se aplica |

O Confluence tem cinco páginas no espaço VELOUR: página inicial, Visão geral e arquitetura, Instalação e execução local, Módulos Financeiro, Fiscal e Contábil, e Cronograma e status das entregas. O manual completo continua em [DOCUMENTACAO.md](../../DOCUMENTACAO.md).

## Divergências encontradas

| Frente | Divergência | Sugestão |
|---|---|---|
| Jira | Todas as issues estão em Concluído, inclusive VEL-54 a VEL-61, com datas de 05/10 a 24/11/2026, ainda futuras. VEL-53, de 21 e 22/09, já passou. | Devolver as tarefas futuras ao estado real. Uma banca que compare o quadro com o calendário vai estranhar uma Banca Final concluída antes de acontecer. |
| Confluence | A página de cronograma diz que todas as fases estão concluídas. A última edição, em 23/09, tem a mensagem "Todas as entregas marcadas como concluídas". | Acompanhar a correção do Jira. |
| Confluence | Cita "projeto Jira VELOUR", mas as chaves das issues começam com `VEL`. `VELOUR` é só a chave do espaço no Confluence. | Corrigir o texto para `VEL`. |
| Jira | VEL-15, "Story: RF01 — Cadastro de Clientes", tem o tipo Tarefa. As demais histórias têm o tipo História. | Trocar o tipo para História. |
| Confluence | A página de cronograma numera os Épicos da disciplina, como "Épico 3 — Financeiro (VEL-22)". Essa numeração não coincide com EP01 a EP12 do Jira. | Explicar a diferença na página, para evitar confusão na banca. |
| Figma | Nenhum arquivo ou link de Figma no repositório, no Jira ou no Confluence. | Montar o protótipo com [prototipo-figma-telas.md](prototipo-figma-telas.md) e linkar nas issues e no Confluence. |
| Código | `npm ci` e `npm run lint` falham por causa do TypeScript 7.0.2. | Fixar o TypeScript em uma versão aceita pelo typescript-eslint. |

Esta análise usou só os títulos das issues e o resumo das páginas do Confluence. Não abri o corpo de cada história para conferir critérios de aceite.
