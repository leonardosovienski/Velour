import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_commit_message', ROOT / 'scripts' / 'check_commit_message.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


@pytest.mark.parametrize('message', [
    'VEL-62: Cria tabela de orçamento de custos',
    'VEL-62 VEL-63: Liga custos ao financeiro\n\nCorpo do commit.',
    'VEL-62, VEL-63: Ajusta testes',
    '# comentário do git\nVEL-7: Corrige agenda',
    'Merge branch \'main\' into feature',
    'Merge pull request #57 from leonardosovienski/branch',
    'Revert "VEL-62: Cria tabela"',
    'fixup! VEL-62: Cria tabela',
])
def test_accepts_jira_key_and_git_generated_messages(message):
    assert checker.is_valid(message)


@pytest.mark.parametrize('message', [
    'feat: add cost module', 'comit', '', 'VEL-62 sem dois-pontos', 'vel-62: minúsculas', 'VEL-0: zero',
    'PI6-12: chave de outro projeto', 'VEL-: sem número', 'VEL-62:sem espaço', 'Prefixo VEL-62: no meio',
])
def test_rejects_messages_without_the_card_key(message):
    assert not checker.is_valid(message)


def test_project_keys_are_configurable(monkeypatch):
    monkeypatch.setenv('JIRA_PROJECT_KEYS', 'pi6, VEL')
    keys = checker.project_keys()
    assert keys == ('PI6', 'VEL')
    assert checker.is_valid('PI6-12: Criada tabela de custos no Banco de Dados', keys)


def test_hook_rejects_and_accepts_message_files(tmp_path, capsys):
    bad, good = tmp_path / 'bad', tmp_path / 'good'
    bad.write_text('ajustes finais\n', encoding='utf-8')
    good.write_text('VEL-62: Ajustes finais\n', encoding='utf-8')
    assert checker.check_file(str(bad)) == 1
    assert 'VEL-<número>' in capsys.readouterr().err
    assert checker.check_file(str(good)) == 0


def test_range_skips_bots_and_merges(tmp_path, monkeypatch):
    def git(*args, author='Pessoa <pessoa@example.com>'):
        name, email = author[:-1].split(' <')
        env = {**os.environ, 'GIT_AUTHOR_NAME': name, 'GIT_AUTHOR_EMAIL': email, 'GIT_COMMITTER_NAME': name,
               'GIT_COMMITTER_EMAIL': email, 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}
        subprocess.run(['git', *args], cwd=tmp_path, check=True, capture_output=True, env=env)
    git('init', '-q', '-b', 'main')
    git('commit', '-q', '--allow-empty', '-m', 'base sem chave')
    git('commit', '-q', '--allow-empty', '-m', 'VEL-1: Com chave')
    git('commit', '-q', '--allow-empty', '-m', 'deps: bump', author='dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>')
    monkeypatch.chdir(tmp_path)
    assert checker.check_range('HEAD~2..HEAD') == 0
    git('commit', '-q', '--allow-empty', '-m', 'sem chave')
    assert checker.check_range('HEAD~3..HEAD') == 1
