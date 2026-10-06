"""Exige a chave do card do Jira no início de cada mensagem de commit.

Regra da disciplina: nenhum commit sem a chave do card (exemplo: "VEL-62: Cria tabela de orçamento de custos").

Uso:
  python scripts/check_commit_message.py .git/COMMIT_EDITMSG     # hook commit-msg (.githooks/commit-msg)
  python scripts/check_commit_message.py --range BASE..HEAD      # CI: commits do pull request

Commits de merge, reverts gerados pelo Git, fixup!/squash! locais e commits de robôs (dependabot[bot],
github-actions[bot]) são ignorados. JIRA_PROJECT_KEYS troca as chaves aceitas (separadas por vírgula).
"""
import os
import re
import subprocess
import sys

DEFAULT_KEYS = ('VEL',)
EXEMPT = re.compile(r'^(Merge (branch|pull request|remote-tracking branch|tag) |Revert "|fixup! |squash! |amend! )')


def project_keys() -> tuple[str, ...]:
    keys = tuple(k.strip().upper() for k in os.getenv('JIRA_PROJECT_KEYS', '').split(',') if k.strip())
    return keys or DEFAULT_KEYS


def pattern(keys: tuple[str, ...]) -> re.Pattern:
    key = '(?:' + '|'.join(re.escape(k) for k in keys) + r')-[1-9]\d*'
    return re.compile(rf'^{key}(?:[ ,]+{key})*: \S')


def first_line(message: str) -> str:
    for line in message.splitlines():
        if line.strip() and not line.startswith('#'):
            return line.strip()
    return ''


def is_valid(message: str, keys: tuple[str, ...] = DEFAULT_KEYS) -> bool:
    line = first_line(message)
    return bool(EXEMPT.match(line) or pattern(keys).match(line))


def is_bot(author: str) -> bool:
    return author.endswith('[bot]') or '[bot]@' in author


def help_text(keys: tuple[str, ...]) -> str:
    sample = f'{keys[0]}-62'
    return (f'A mensagem precisa começar com a chave do card do Jira ({", ".join(k + "-<número>" for k in keys)}), '
            f'dois-pontos e a descrição.\nExemplo: git commit -m "{sample}: Cria tabela de orçamento de custos"')


def check_file(path: str) -> int:
    keys = project_keys()
    with open(path, encoding='utf-8') as handle:
        message = handle.read()
    if is_valid(message, keys):
        return 0
    print(f'Commit recusado: "{first_line(message)}"\n{help_text(keys)}', file=sys.stderr)
    return 1


def check_range(revision_range: str) -> int:
    keys = project_keys()
    log = subprocess.run(['git', 'log', '--no-merges', '--format=%H%x1f%an%x1f%ae%x1f%B%x1e', revision_range],
                         check=True, capture_output=True, text=True, encoding='utf-8').stdout
    failures = []
    for record in filter(str.strip, log.split('\x1e')):
        sha, name, email, body = record.strip('\n').split('\x1f', 3)
        if is_bot(name) or is_bot(email) or is_valid(body, keys):
            continue
        failures.append(f'{sha[:10]} {first_line(body)}')
    if failures:
        print('Commits sem a chave do card do Jira:\n  ' + '\n  '.join(failures) + '\n' + help_text(keys), file=sys.stderr)
        return 1
    print('Todos os commits citam um card do Jira.')
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == '--range':
        return check_range(argv[1])
    if len(argv) == 1:
        return check_file(argv[0])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
