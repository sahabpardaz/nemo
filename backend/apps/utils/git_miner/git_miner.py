import subprocess
from tempfile import TemporaryDirectory
import traceback
import re
from datetime import datetime
from typing import Generator
from apps.utils.url import get_authorized_url
from apps.utils import os_utils
from apps.utils.git_miner.commit import Commit
from apps.utils.git_miner.git_command_exception import GitCommandException


class GitMiner:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def traverse_commits_back(self) -> Generator[Commit, None, None]:
        try:
            result = os_utils.run_cmd(['git', 'log', '--pretty=fuller'], self.repo_path, raise_on_non_zero_code=True)
        except subprocess.CalledProcessError as e:
            raise GitCommandException(e)
        lines_iterator = iter(result.stdout.decode('utf-8').split('\n'))
        while True:
            try:
                line = next(lines_iterator)
            except StopIteration:
                break
            try:
                sha = GitMiner._remove_substr(line, '^commit ( )*')

                line = next(lines_iterator)
                is_merge = not not re.match('^Merge: ( )*', line)
                if is_merge:
                    line = next(lines_iterator)
                author = GitMiner._remove_substr(line, '^Author: ( )*')

                line = next(lines_iterator)
                author_date = GitMiner._str_to_datetime(GitMiner._remove_substr(line, '^AuthorDate: ( )*'))

                line = next(lines_iterator)
                committer = GitMiner._remove_substr(line, '^Commit: ( )*')

                line = next(lines_iterator)
                commit_date = GitMiner._str_to_datetime(GitMiner._remove_substr(line, '^CommitDate: ( )*'))

                line = next(lines_iterator)
                assert line == ""
                line = next(lines_iterator)
                title = GitMiner._remove_substr(line, '^( )*')

                body = ""
                while True:
                    line = next(lines_iterator)
                    if line == "":
                        break
                    body += GitMiner._remove_substr(line, '^( )*')
                    body += '\n'

                yield Commit(sha, author, author_date, committer, commit_date, title, body, is_merge)
            except StopIteration:
                raise Exception('Unexpected end of commit log')

    @staticmethod
    def _str_to_datetime(s):
        return datetime.strptime(s, '%a %b %d %H:%M:%S %Y %z')

    @staticmethod
    def _remove_substr(txt, substr):
        if not re.match(substr, txt):
            raise Exception(f"String '{txt}' doesn't contain the expected substr: '{substr}'")
        return re.sub(substr, '', txt)


class _GitMinerResource:
    def __init__(self, url: str, branch: str):
        self.url = url
        self.branch = branch

    def __enter__(self):
        self.tmp_dir = TemporaryDirectory()
        self.repo_path = self.tmp_dir.__enter__()
        try:
            # TODO Consider handling large size repos
            os_utils.run_cmd(['git', 'clone', '-b', self.branch, '--single-branch', '--no-checkout', self.url, self.repo_path],
                             raise_on_non_zero_code=True)
        except Exception as e:
            self.tmp_dir.__exit__(type(e), e, traceback.extract_stack())
            if isinstance(e, subprocess.CalledProcessError):
                if f'fatal: Remote branch {self.branch} not found' in str(e.stderr.decode('utf-8')):
                    raise GitCommandException(e)
            raise
        return GitMiner(self.repo_path)

    def __exit__(self, exc_type, exc_value, traceback):
        self.tmp_dir.__exit__(exc_type, exc_value, traceback)

class GitMinerFactory:

    @staticmethod
    def from_url(url: str, branch: str = 'master', username: str = None, password: str = None) -> _GitMinerResource:
        authorized_url = get_authorized_url(url, username, password)
        return _GitMinerResource(authorized_url, branch)
