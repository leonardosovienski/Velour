# Security Policy

## Supported Versions

O projeto está em desenvolvimento ativo. Correções de segurança são aplicadas na branch `main` e, quando houver releases publicadas, na versão mais recente.

| Versão | Suporte de segurança |
|---|---|
| `main` | ✅ |
| release mais recente | ✅ |
| versões antigas | ❌ |

## Reporting a Vulnerability

Não abra uma issue pública para relatar vulnerabilidades.

Use o recurso **Private vulnerability reporting** disponível na aba **Security** deste repositório.

Inclua, quando possível:

- descrição clara da vulnerabilidade;
- componente, endpoint ou arquivo afetado;
- passos para reproduzir;
- impacto esperado;
- evidências sanitizadas;
- sugestão de correção, caso exista.

Não envie credenciais reais, tokens válidos, dados pessoais, fotos de clientes, arquivos de produção ou informações sensíveis como prova.

## Security Scope

Estão dentro do escopo:

- backend FastAPI e endpoints REST;
- autenticação, JWT e expiração de sessão;
- autorização, RBAC e controles de acesso;
- validação de entrada e regras de negócio;
- upload, armazenamento e entrega de arquivos;
- proteção contra path traversal e arquivos maliciosos;
- acesso ao banco de dados e integridade transacional;
- agendamentos, estoque, fidelidade e indicações;
- tarefas agendadas e processamento em segundo plano;
- frontend React e tratamento de sessão;
- dependências Python e npm;
- workflows do GitHub Actions;
- tratamento de segredos e variáveis de ambiente.

Não estão dentro do escopo:

- indisponibilidade de serviços externos;
- falhas exclusivamente em bibliotecas de terceiros já corrigidas na versão mais recente;
- engenharia social;
- ataques que dependam de credenciais já comprometidas fora do projeto;
- uso do sistema fora das instruções documentadas;
- problemas já corrigidos na branch `main`.

## Sensitive Data

O projeto pode processar dados como:

- nome, telefone e e-mail de clientes;
- data de nascimento;
- alergias e preferências pessoais;
- histórico de atendimentos;
- fotos antes e depois de procedimentos;
- informações financeiras e de fidelidade.

Esses dados não devem ser usados em testes públicos, issues, screenshots ou relatórios de vulnerabilidade. Utilize dados fictícios e evidências sanitizadas.

## Secrets

Nunca faça commit de:

- `.env`;
- `SECRET_KEY` de JWT;
- tokens de API;
- senhas reais;
- credenciais de banco;
- arquivos de produção;
- bancos SQLite contendo dados pessoais;
- uploads reais de clientes.

Caso um segredo seja exposto, removê-lo do código não é suficiente. Ele deve ser revogado ou rotacionado imediatamente no provedor correspondente.

## Response Process

Após o recebimento de um relato:

1. o problema será analisado;
2. severidade, impacto e alcance serão avaliados;
3. uma correção será preparada, quando necessária;
4. credenciais comprometidas deverão ser revogadas ou rotacionadas;
5. testes de regressão serão adicionados quando aplicável;
6. a divulgação pública ocorrerá somente após a correção, quando necessário.

Não há garantia de prazo fixo de resposta, pois este é um projeto pessoal mantido individualmente.

## Safe Testing

Ao testar o projeto:

- use dados fictícios;
- não ataque ambientes de terceiros;
- não tente acessar dados de outros usuários;
- não cause indisponibilidade deliberada;
- não mantenha cópias de dados obtidos durante a investigação;
- pare o teste assim que houver evidência suficiente da vulnerabilidade.
