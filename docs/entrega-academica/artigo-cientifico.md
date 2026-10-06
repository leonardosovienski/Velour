# Rascunho do artigo científico

Este texto é um ponto de partida. Todos os fatos técnicos vêm do código e da documentação do repositório e dos testes de 29/09/2026. Antes de entregar:

- Preencha autores, orientação e instituição, e adapte a formatação ao modelo exigido pela UNIFACEAR, que não foi consultado.
- Confira as referências na biblioteca. Foram citadas de memória e podem ter edição ou ano diferentes.
- Não há dados de uso real por salões nem pesquisa com usuários. O texto não afirma nenhum. Se o grupo tiver esses dados, inclua-os na seção 5.

---

# Velour: arquitetura e regras de negócio de um SaaS multi-salão para gestão de salões de beleza

**Autores:** [nomes dos integrantes]
**Instituição:** [UNIFACEAR, curso de Tecnologia da Informação]
**Disciplina:** Projeto Integrador VI, 2º semestre de 2026

## Resumo

Este trabalho apresenta o Velour, um sistema de gestão para salões de beleza oferecido como software como serviço, desenvolvido como projeto integrador. O sistema reúne agenda, clientes, profissionais, serviços, estoque, programa de fidelidade e indicações, relatórios, assinatura mensal e módulos demonstrativos financeiro, fiscal e contábil. O frontend usa React e TypeScript, e o backend usa FastAPI e SQLAlchemy, com PostgreSQL em produção. Cada salão tem dados, usuários e assinatura isolados, e o escopo é definido pela autenticação, não por dados do cliente. O artigo descreve a arquitetura, as regras de domínio e o processo de desenvolvimento com Scrum, Jira, Confluence e Figma. Em ambiente controlado, 212 testes automatizados do backend, sendo 6 em PostgreSQL, e 56 do frontend foram aprovados. Os módulos fiscal e contábil não têm validade legal, e a cobrança com Stripe e o envio de e-mails não foram homologados com credenciais reais. Conclui-se que o sistema cumpre os requisitos funcionais propostos e indica os passos necessários para uso comercial.

**Palavras-chave:** software como serviço; multi-inquilino; gestão de salões; FastAPI; React.

## Abstract

This paper presents Velour, a software-as-a-service platform for beauty salon management built as a capstone project. It provides scheduling, client records, staff, services, inventory, a loyalty and referral program, reports, monthly subscription billing and demonstrative finance, tax and accounting modules. The frontend uses React and TypeScript; the backend uses FastAPI and SQLAlchemy, with PostgreSQL in production. Each salon has isolated data, users and subscription, and the scope is derived from authentication rather than client-supplied data. The paper describes the architecture, the domain rules and the development process based on Scrum, Jira, Confluence and Figma. In a controlled environment, 212 backend automated tests, 6 of them on PostgreSQL, and 56 frontend tests passed. The tax and accounting modules have no legal validity, and Stripe billing and email delivery were not validated with real credentials.

**Keywords:** software as a service; multi-tenancy; salon management; FastAPI; React.

## 1 Introdução

Salões de beleza lidam com agenda de profissionais, cadastro e preferências de clientes, consumo de insumos e relacionamento para retorno. O projeto parte da premissa de que essas rotinas se beneficiam de um sistema único, acessível pelo navegador e contratado por assinatura, sem instalação local.

O objetivo geral é desenvolver e documentar um SaaS de gestão de salões em que cada salão opere apenas sobre os próprios dados. Os objetivos específicos são:

1. Implementar agenda com controle de conflitos e conclusão de atendimento com efeitos financeiros e de fidelidade consistentes.
2. Isolar dados e permissões por salão e por papel de usuário.
3. Oferecer assinatura mensal com período de teste.
4. Documentar o processo em Jira, Confluence e Figma, em alinhamento com o código.
5. Verificar o sistema por testes automatizados e declarar seus limites.

## 2 Referencial teórico

**Software como serviço e multi-inquilino.** No modelo SaaS, uma única instância atende vários clientes, chamados inquilinos. Bezemer e Zaidman (2010) discutem os desafios de manutenção dessas aplicações. No Velour, o inquilino é o salão, e o isolamento é feito por coluna de identificação em cada registro operacional.

**Desenvolvimento ágil.** Scrum organiza o trabalho em entregas incrementais curtas (SCHWABER; SUTHERLAND, 2020). A disciplina adota uma dinâmica gamificada nesse modelo, com entregas parciais por Épico.

**Requisitos e qualidade.** Sommerville (2018) e Pressman e Maxim (2021) tratam engenharia de requisitos, testes e verificação, que orientam a organização em épicos e histórias com critérios de aceite.

**Segurança de aplicações.** O Application Security Verification Standard da OWASP (2021) lista controles de autenticação, controle de acesso e proteção de dados. Foi usado como referência de lista de verificação, sem declarar conformidade formal.

## 3 Metodologia

O trabalho seguiu o Scrum da disciplina, com entregas por Épico ao longo do semestre. No Jira, o projeto `VEL` tem 12 épicos, de EP01 a EP12, e histórias que descrevem as funcionalidades entregues. O Confluence, no espaço `VELOUR`, guarda a visão geral e a arquitetura, a instalação, os módulos financeiro, fiscal e contábil e o cronograma. O protótipo de interface é feito no Figma [preencher após criar o arquivo]. O código está em repositório Git com integração contínua.

Os épicos são: autenticação e acesso; clientes; agenda e atendimentos; profissionais e serviços; estoque e ficha técnica; fidelidade e indicações; dashboard e relatórios; SaaS, multi-salão e assinatura; financeiro; fiscal; contábil; e entregas acadêmicas. A rastreabilidade entre épicos, código, telas e testes está em [matriz-alinhamento.md](matriz-alinhamento.md).

## 4 Desenvolvimento

### 4.1 Arquitetura

O navegador executa uma aplicação React com TypeScript. Ela se comunica pelo caminho `/api` com uma API FastAPI, que usa SQLAlchemy sobre PostgreSQL. A API integra o Stripe para assinatura, um servidor SMTP para e-mails e um volume privado para fotos. Em desenvolvimento, o banco é SQLite. A versão de produção suportada tem uma única réplica da API, e um bloqueio consultivo do PostgreSQL impede uma segunda instância no mesmo banco. As páginas do frontend são carregadas sob demanda, e o pacote inicial tem cerca de 325 kB, ou 105 kB comprimido.

### 4.2 Isolamento por salão e controle de acesso

Toda consulta operacional passa por uma sessão com escopo de salão, definido pela autenticação. Os registros carregam a identificação do salão, e o banco impõe restrições compostas para que referências entre entidades pertençam ao mesmo salão. O token de sessão identifica salão e usuário, mas o papel e o estado são verificados no banco a cada requisição. Mudanças de papel e recuperação de senha incrementam uma versão que revoga tokens anteriores. Existem três papéis. Administrador e gerente operam o salão, e apenas o administrador gerencia cobrança, exportação e outros administradores. O profissional acessa só os próprios atendimentos e os clientes vinculados a eles. Os testes cobrem acesso a registros e fotos de outro salão, escritas e reutilização de objetos em memória.

### 4.3 Assinatura

O cadastro cria um salão e seu primeiro administrador com 14 dias de teste. A assinatura é um plano mensal no Stripe, contratado por Checkout e gerenciado pelo Portal, sem que o sistema colete dados de cartão. O acesso às rotas de negócio depende da situação da assinatura: teste vigente, assinatura ativa ou até 7 dias após início da inadimplência. Fora disso a API responde 402. Eventos do Stripe são aceitos só com assinatura válida e conferidos contra o estado atual no provedor.

### 4.4 Regras de domínio

**Agenda.** O servidor calcula o fim do atendimento somando a duração do serviço. Há conflito quando o intervalo se sobrepõe ao de outro atendimento do mesmo profissional, e a API responde 409. Atendimentos adjacentes são permitidos, e cancelados e faltas não ocupam horário. Datas são horários locais sem fuso, e valores com fuso são rejeitados.

**Conclusão do atendimento.** A conclusão é uma transação única que grava cobrança, descontos, pontos, nível, indicação e consumo de estoque. Repetir a conclusão retorna conflito e não repete os efeitos.

**Fidelidade.** O desconto depende do nível do cliente antes do atendimento, conforme a tabela.

| Nível | Gasto acumulado | Desconto |
|---|---|---|
| Bronze | Menos de R$ 500 | 0% |
| Silver | R$ 500 a menos de R$ 1.500 | 5% |
| Gold | R$ 1.500 a menos de R$ 3.000 | 10% |
| Platinum | R$ 3.000 ou mais | 15% |

O resgate de pontos é feito em múltiplos de 100, e cada 100 pontos valem R$ 10. Nível e resgate somados não passam de 50% do valor base. O primeiro atendimento concluído de um cliente indicado converte a indicação, com 150 pontos para quem indicou e 75 para o indicado. O bônus de aniversário é de 100 pontos, com consulta ao histórico para não se repetir no mês.

**Estoque.** Cada serviço tem uma ficha técnica de insumos. A conclusão baixa o consumo e registra um movimento, e o saldo pode ficar negativo, gerando alerta de reposição. Perdas manuais acima do saldo são rejeitadas.

**Valores monetários.** O sistema usa aritmética decimal no backend e números JSON nas respostas, sem converter os valores internos para ponto flutuante.

### 4.5 Módulos financeiro, de custos, fiscal e contábil

O módulo financeiro registra recebimentos e despesas por salão e resume o mês. Os módulos fiscal e contábil são demonstrações acadêmicas. O fiscal simula a emissão de notas de serviço sem transmitir nada à Receita ou à prefeitura. O contábil gera DRE, livro diário e balancete demonstrativos, com exportação em TXT e PDF. Nenhum dos dois tem validade fiscal ou contábil.

A gestão de custos aplica o custeio variável aos mesmos registros. Insumos consumidos, comissões e ISS estimado são custos variáveis. As despesas, pelo vencimento, são custos fixos. A partir deles, o sistema calcula a margem de contribuição, o ponto de equilíbrio, que é o custo fixo dividido pelo índice de margem de contribuição, e a margem de segurança. Mostra ainda a margem por serviço e por profissional e o custo-padrão de cada serviço pela ficha técnica. O orçamento mensal por linha de custo é a única informação gravada pelo módulo. O sistema compara esse orçamento ao realizado e emite alertas quando uma linha estoura o orçamento, quando um serviço tem margem negativa ou quando o preço não cobre insumos e imposto.

## 5 Verificação e resultados

A verificação de 29/09/2026 ocorreu em um contêiner Linux com Python 3.11, Node 22 e PostgreSQL 16, diferente da integração contínua do projeto, que usa Python 3.12 e 3.13 e Node 24, e da produção prevista, que usa PostgreSQL 17.

| Verificação | Resultado |
|---|---|
| Testes do backend, SQLite em memória | 206 aprovados e 6 pulados |
| Testes de isolamento entre salões, PostgreSQL | 6 aprovados |
| Migrações em banco vazio e verificação de divergências | Concluídas, sem divergências |
| Auditoria de dependências Python | Nenhuma vulnerabilidade conhecida |
| Testes do frontend | 56 aprovados, em 16 arquivos |
| Análise estática e build do frontend | Aprovados |
| Auditoria de dependências do frontend | Nenhuma vulnerabilidade de gravidade alta |
| Navegação por 16 telas em navegador, com dados fictícios | Todas carregaram, sem falha de API |
| Fluxos de agenda, conclusão e permissões pela API, com dados fictícios | Comportamento conforme as regras descritas na seção 4 |

Não foram executados nessa rodada os containers, o backup com restauração e o teste de migração a partir de uma base existente. A navegação em navegador cobriu o perfil de administrador. Um resultado de testes aprovados sustenta a verificação local, mas não equivale a homologação para clientes reais.

## 6 Limitações

- Os módulos fiscal e contábil são demonstrativos.
- Stripe e SMTP têm implementação e testes locais, mas não foram homologados com contas reais.
- A implantação suportada tem uma única réplica da API. Limites de requisições, bloqueios e agendadores são locais ao processo.
- Não há fila durável de e-mails nem garantia de entrega única.
- O fuso horário é único por implantação, não por salão.
- Os clientes do salão são registros do sistema e não têm portal próprio de agendamento.
- Não houve avaliação com usuários reais.

## 7 Conclusão

O Velour implementa os requisitos funcionais propostos para agenda, clientes, profissionais, serviços, estoque, fidelidade, relatórios, assinatura e módulos demonstrativos, com isolamento de dados por salão verificado por testes automatizados. Para uso comercial, ainda são necessárias a homologação de pagamentos e e-mail, a infraestrutura de produção com backup externo e monitoramento e a validação com salões reais. Como trabalhos futuros, ficam a integração fiscal real, o portal do cliente, o fuso por salão e a fila durável de mensagens.

## Referências

BEZEMER, C.-P.; ZAIDMAN, A. Multi-tenant SaaS applications: maintenance dream or nightmare? In: INTERNATIONAL WORKSHOP ON PRINCIPLES OF SOFTWARE EVOLUTION, 2010. **Proceedings** [...]. ACM, 2010. [conferir dados da publicação]

OWASP. **Application Security Verification Standard 4.0.3**. 2021. [conferir endereço e data de acesso]

PRESSMAN, R. S.; MAXIM, B. R. **Engenharia de software**: uma abordagem profissional. 9. ed. Porto Alegre: AMGH, 2021. [conferir]

SCHWABER, K.; SUTHERLAND, J. **The Scrum Guide**. 2020. [conferir endereço e data de acesso]

SOMMERVILLE, I. **Engenharia de software**. 10. ed. São Paulo: Pearson, 2018. [conferir]
