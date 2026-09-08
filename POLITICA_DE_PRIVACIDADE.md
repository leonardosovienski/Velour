# Política de Privacidade — Velour SaaS

**Minuta para preenchimento e revisão antes da publicação.** Revisão técnica: 8 de setembro de 2026. Esta descrição corresponde ao código do repositório; provedores, retenção, canais e procedimentos da operação comercial ainda precisam ser preenchidos e verificados.

## 1. Responsável e canais

Fornecedor: **[RAZÃO SOCIAL]**, CNPJ **[CNPJ]**, endereço **[ENDEREÇO]**. Canal para assuntos de privacidade e identificação do encarregado, quando aplicável: **[PREENCHER]**.

O fornecedor trata dados para operar contas, autenticação, cobrança, segurança e suporte. Quanto aos registros que o salão insere para atender seus próprios clientes, os papéis e instruções devem ser definidos no Anexo de Tratamento de Dados abaixo. A qualificação de controlador ou operador depende das decisões e atividades efetivas de cada parte, conforme a [LGPD, art. 5º](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm).

## 2. Dados da conta e do funcionamento

| Categoria | Dados tratados pela implementação |
| --- | --- |
| Salão | Nome, identificador, slug, situação da conta, datas de criação/teste/assinatura e versão/data do aceite inicial |
| Usuários | Nome, e-mail, papel, vínculo profissional quando houver, situação ativa, hash de senha e versão de sessão |
| Cobrança | Identificadores de cliente, assinatura, Checkout e eventos Stripe; situação e datas da assinatura |
| Recuperação de senha | E-mail destinatário, resumo criptográfico do token, expiração e utilização |
| Operação e segurança | Registros técnicos e de auditoria, horários, ações, identificadores e endereços IP conforme o componente |

O formulário inicial do Velour não solicita CNPJ/CPF, endereço ou razão social como campos próprios. O Checkout pode solicitar dados de faturamento conforme a configuração do Stripe. Não são armazenados número completo de cartão ou CVV no banco da aplicação.

As finalidades são fornecer acesso ao serviço, administrar a assinatura, recuperar contas, prestar suporte e investigar falhas ou uso indevido. O fornecedor deve documentar **[BASE LEGAL POR FINALIDADE E JUSTIFICATIVA, CONFORME SUA OPERAÇÃO]**. O aceite dos termos não deve ser tratado como autorização genérica para qualquer uso de dados.

## 3. Navegador e serviços externos

A sessão utiliza um token no `sessionStorage` do navegador, enviado nas requisições autenticadas. Ele não substitui a verificação de autorização no servidor. O link de recuperação contém um token temporário; não deve ser compartilhado. O proxy fornecido evita registrar consultas de URL e cabeçalhos sensíveis nos formatos de log configurados.

O código atual não inclui ferramenta de publicidade ou analytics. A página carrega fontes do Google Fonts, o que gera requisições externas com informações técnicas da conexão. Stripe Checkout e Customer Portal são páginas hospedadas pelo Stripe e podem utilizar seus próprios mecanismos de armazenamento e tratamento. O fornecedor deve conferir a política aplicável a esses serviços e a qualquer ferramenta que venha a adicionar.

Antes da publicação, completar o inventário real:

| Serviço | Uso | Informação pendente |
| --- | --- | --- |
| Stripe | Assinatura e portal de cobrança do salão | [ENTIDADE CONTRATADA, POLÍTICA E REGIÕES APLICÁVEIS] |
| Hospedagem e banco | Aplicação, registros e fotos | [PROVEDOR, REGIÃO E ACESSOS] |
| SMTP | Recuperação de senha e notificações habilitadas | [PROVEDOR, POLÍTICA E REGIÃO] |
| Armazenamento externo | Cópias de segurança | [PROVEDOR, REGIÃO, PROTEÇÃO E RETENÇÃO] |
| Google Fonts | Carregamento das fontes da interface | [VALIDAR POLÍTICA E USO NA IMPLANTAÇÃO] |

Se houver tratamento fora do Brasil, o fornecedor e o salão devem avaliar as condições e mecanismos aplicáveis. Nenhuma região de armazenamento ou transferência internacional foi presumida nesta minuta.

## 4. Retenção e segurança

Períodos e critérios de retenção precisam ser publicados para **[CONTAS]**, **[REGISTROS DE CLIENTES]**, **[FOTOS]**, **[LOGS]**, **[DOCUMENTOS DE COBRANÇA]** e **[BACKUPS]**, com responsáveis por execução e verificação.

Cancelar uma assinatura não elimina dados. As funções de desativação preservam histórico; excluir um registro pela interface não equivale a um processo completo de eliminação de dados pessoais. Pedidos de anonimização ou eliminação exigem procedimento assistido que considere vínculos, cópias de segurança e retenções aplicáveis. Não existe prazo automático de eliminação implementado.

O código oferece hash de senhas, tokens com expiração, isolamento por salão, permissões por papel, validação e acesso autenticado às fotos, revogação de sessões e auditoria de ações específicas. O guia de implantação prevê HTTPS. Criptografia de volumes e backups, armazenamento externo, gestão de acesso do operador e alertas dependem da infraestrutura configurada. Não se presume certificação, alta disponibilidade ou auditoria independente.

## 5. Solicitações dos titulares

Os titulares podem exercer os direitos aplicáveis, incluindo confirmação, acesso e correção, e solicitar anonimização, bloqueio ou eliminação nas hipóteses legais. Veja a [LGPD, art. 18](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm). O atendimento deve verificar a identidade e os limites legais sem coletar informações excessivas.

Pedidos sobre conta e cobrança: **[CANAL DO FORNECEDOR]**. Pedidos de clientes finais sobre seus atendimentos: o salão responsável, com apoio do fornecedor quando necessário. Procedimento, responsável e prazos de atendimento: **[DEFINIR CONFORME AS OBRIGAÇÕES APLICÁVEIS]**.

A exportação do administrador é um arquivo JSON dos registros do salão, sem hashes de senha, segredos ou tokens de recuperação. Fotos são referências autenticadas para download separado. Ela auxilia o atendimento, mas não realiza automaticamente a seleção de dados de um titular nem a anonimização dos demais.

## 6. Anexo de Tratamento de Dados — registros do salão

### 6.1 Escopo e instruções

O salão determina os registros necessários ao atendimento e gestão do seu negócio. O fornecedor executa o armazenamento e processamento previstos no serviço, de acordo com as instruções contratadas. Detalhar **[INSTRUÇÕES, PESSOAS AUTORIZADAS, CONFIDENCIALIDADE, SUBCONTRATAÇÃO E ASSISTÊNCIA]** no acordo entre as partes.

Os registros podem incluir:

- Nome, telefone, e-mail, gênero e nascimento dos clientes.
- Preferências de atendimento, alergias e observações da equipe.
- Agendamentos, profissionais, serviços, valores e forma de pagamento registrada.
- Fotos de antes/depois e fórmulas de coloração.
- Pontos, benefícios e indicações de fidelidade.
- Contatos e informações profissionais da equipe, incluindo comissão e metas.

Os dados servem à operação das funcionalidades contratadas. Notificações por e-mail de agendamento dependem da configuração do SMTP e das opções do cadastro. O envio envolve o destinatário e o conteúdo necessário ao aviso.

### 6.2 Dados sensíveis, fotos e menores

Informações de saúde, como alergias, podem ser dados pessoais sensíveis e exigem avaliação das hipóteses do art. 11. Registros de crianças e adolescentes exigem consideração de seu melhor interesse e das condições do art. 14. Consulte a [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm).

O salão deve definir necessidade, base legal e acesso apropriado antes de registrar essas informações. A aplicação não coleta nem administra automaticamente autorizações específicas para fotos, dados de saúde ou atendimento de menores. O aceite do administrador no cadastro do salão não substitui esses procedimentos.

### 6.3 Incidentes, solicitações e encerramento

As partes devem definir **[CANAL DE INCIDENTES, RESPONSÁVEIS, PROCEDIMENTO E PRAZOS]**, incluindo informações para avaliação e cumprimento das obrigações de comunicação aplicáveis. Não há comunicação automática a titulares ou à ANPD no software.

Também devem definir o processo para exportação, correção, restrição, anonimização e eliminação ao final do contrato, abrangendo banco, fotos e backups. Uma conta suspensa perde o acesso à aplicação; seu atendimento dependerá do canal do fornecedor.

## 7. Publicação e mudanças

Preencher todos os campos pendentes e confirmar que os processos descritos existem antes de publicar. Definir **[COMO E QUANDO MUDANÇAS SERÃO COMUNICADAS]**, conservar versões anteriores e manter o canal de privacidade acessível. Configure o endereço HTTPS final em `PRIVACY_URL`, conforme o [guia de produção](PRODUCTION.md).
