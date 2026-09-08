# Termos de Uso — Velour SaaS

**Minuta para preenchimento e revisão antes da publicação.** Revisão técnica: 8 de setembro de 2026. Os campos entre colchetes dependem da empresa que comercializará o serviço; este arquivo não é um contrato já aprovado ou publicado.

## 1. Fornecedor e contratação

A plataforma Velour é fornecida por **[RAZÃO SOCIAL]**, inscrita no CNPJ sob **[CNPJ]**, com sede em **[ENDEREÇO]**. Contato contratual e de suporte: **[E-MAIL OU CANAL DE SUPORTE]**. Contato de privacidade: **[CANAL DE PRIVACIDADE]**.

O contratante é o estabelecimento que cria uma conta para gerir seu salão. O responsável pelo cadastro deve estar autorizado a contratar em nome do estabelecimento. No cadastro, ele informa o nome do salão, seu nome, e-mail, senha e aceite dos documentos apresentados. A plataforma registra a data do aceite e a versão dos termos configurada naquele momento.

A [Política de Privacidade](POLITICA_DE_PRIVACIDADE.md), incluindo seu Anexo de Tratamento de Dados, acompanha estes termos. Na publicação, substitua os links relativos deste repositório pelas páginas públicas correspondentes.

## 2. Serviço e contas

O serviço oferece agenda, clientes, profissionais, serviços, estoque, fidelidade, indicações e relatórios. Cada salão possui seus próprios registros. Seus usuários têm papel de administrador, gerente ou profissional, com as permissões descritas no [manual funcional](DOCUMENTACAO.md).

O administrador gerencia a equipe, a assinatura e a exportação. Um e-mail identifica uma única conta na plataforma; a mesma conta não pertence a vários salões. O estabelecimento deve manter os dados de contato corretos, conceder acesso somente à equipe autorizada e comunicar suspeitas de uso indevido pelo canal de suporte.

O registro da forma de pagamento de um atendimento é uma anotação de gestão. O Velour não processa o pagamento do cliente final ao salão nem emite automaticamente documentos fiscais. O Stripe processa a assinatura do software contratada pelo salão.

## 3. Teste, preço e cobrança

Novos cadastros recebem 14 dias de teste sem cartão. A continuidade das operações de negócio após o teste depende da assinatura. A configuração atual oferece uma assinatura mensal por salão, com quantidade 1, pelo preço mostrado no Stripe Checkout antes da confirmação.

Quando a contratação ocorre durante o teste, o Checkout informa a data da primeira cobrança. Próximo do vencimento, a integração pode estender o período até 49 horas a partir da abertura do Checkout. O pagamento e o acesso são confirmados pelo processamento dos eventos do Stripe; a página de retorno, isoladamente, não ativa a assinatura.

Preencher e apresentar ao cliente antes da contratação:

| Condição comercial | Informação a publicar |
| --- | --- |
| Preço e moeda | [VALOR MENSAL E MOEDA, COERENTES COM O PRICE DO STRIPE] |
| Tributos e documento fiscal | [RESPONSÁVEL, INCLUSÃO NO PREÇO E PROCESSO DE EMISSÃO] |
| Reajustes e alterações de plano | [CRITÉRIO E FORMA/PRAZO DE COMUNICAÇÃO] |
| Cancelamento | [EFEITO IMEDIATO OU AO FIM DO CICLO, CONFORME O PORTAL CONFIGURADO] |
| Reembolso e direitos aplicáveis | [POLÍTICA REVISADA PARA O MERCADO E CONTRATANTE ATENDIDOS] |

A integração permite carência de até 7 dias para assinatura em atraso, calculada a partir da fatura não paga. Sem direito de acesso, o sistema bloqueia as operações de negócio e direciona a regularização à tela Assinatura. O estabelecimento deve conferir os valores, datas e condições exibidos no Checkout antes de confirmar.

## 4. Cancelamento, suspensão e dados

O administrador acessa o portal de cobrança pela tela Assinatura para gerenciar pagamento e cancelamento, de acordo com as opções habilitadas pelo fornecedor no Stripe. A data de encerramento deve ser a informada pelo portal. Cancelar a assinatura não apaga a conta nem os dados.

Enquanto a conta permanecer ativa na plataforma, o vencimento do teste ou da assinatura preserva login, cobrança, exportação do administrador e leitura autorizada de fotos. A exportação contém registros em JSON; fotos são referências que exigem autenticação para download separado. Uma conta suspensa pelo operador perde acesso, inclusive a essas funções, e deve recorrer ao suporte.

O fornecedor precisa definir e publicar **[MOTIVOS E PROCEDIMENTO DE SUSPENSÃO, COMUNICAÇÃO E CONTESTAÇÃO]**, **[PRAZO DE DISPONIBILIDADE DOS DADOS APÓS ENCERRAMENTO]** e **[RETENÇÃO E ELIMINAÇÃO, INCLUINDO BACKUPS]**. A plataforma não executa eliminação automática ao cancelar. Desativar clientes, profissionais ou usuários preserva seu histórico; outras exclusões dependem do tipo de registro e de seus vínculos.

## 5. Responsabilidades sobre dados pessoais

O estabelecimento decide quais dados de seus clientes e equipe registrar e deve limitar o uso às finalidades informadas. Alergias, informações de saúde, fotos e registros de menores exigem avaliação específica das condições de tratamento. Os papéis e o procedimento de atendimento de solicitações estão descritos no anexo da política.

O fornecedor deve operar o serviço conforme as instruções contratadas e os compromissos de proteção de dados efetivamente implementados. O estabelecimento deve orientar sua equipe a não inserir credenciais, dados de cartão ou informações desnecessárias em campos de observação.

## 6. Suporte e disponibilidade

Canal, dias e horários de atendimento: **[DEFINIR]**. Prazo de resposta e eventual compromisso de disponibilidade: **[DEFINIR]**. Janelas de manutenção e comunicação de indisponibilidade: **[DEFINIR]**.

A versão atual utiliza uma única API e admite interrupções de manutenção, inclusive no backup consistente. E-mails dependem do provedor SMTP e cobranças dependem do Stripe. O contrato deve refletir a infraestrutura contratada, o monitoramento e a recuperação efetivamente testados. O software não estabelece um SLA numérico.

## 7. Direitos de uso e responsabilidades contratuais

Definir, após conferir a titularidade do código, marca e licenças de dependências: **[DIREITOS CONCEDIDOS AO CONTRATANTE E RESTRIÇÕES DE USO]**. Este documento não transfere o código-fonte nem comprova titularidade de marca.

Preencher com revisão jurídica: **[RESPONSABILIDADES DAS PARTES, EVENTUAIS LIMITAÇÕES ADMISSÍVEIS E SOLUÇÃO DE CONTROVÉRSIAS]**, preservando os direitos obrigatórios aplicáveis ao contratante. Não há cláusula de isenção geral presumida por esta minuta.

## 8. Atualizações e contato

Forma de comunicação de mudanças contratuais, antecedência e novo aceite quando necessário: **[DEFINIR]**. A plataforma registra o aceite inicial; não implementa um fluxo geral de novo aceite para todas as contas existentes. O fornecedor deve organizar a comunicação e conservar as versões publicadas.

Antes de habilitar cadastros, finalize os campos pendentes, publique estes termos e a política em HTTPS e configure `TERMS_URL`, `PRIVACY_URL` e `TERMS_VERSION`, conforme o [guia de produção](PRODUCTION.md).
