from datetime import datetime
import os
import shutil
import tempfile
from typing import List
from django.test import TestCase
from apps.utils import os_utils
from apps.utils.git_miner.git_miner import GitMiner, GitMinerFactory


class GitMinerTest(TestCase):
    def setUp(self) -> None:
        self.repo_path = tempfile.mkdtemp()
        self._cmd_git(['init'])
        self.git_user_email = 'test@test.com'
        self.git_user_name = 'test user'
        self._cmd_git(['config', 'user.email', self.git_user_email])
        self._cmd_git(['config', 'user.name', self.git_user_name])
        self.git_miner = GitMiner(self.repo_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.repo_path)

    def _cmd_git(self, cmd: List[str]):
        os_utils.run_cmd(['git'] + cmd, cwd=self.repo_path, raise_on_non_zero_code=True)

    def _git_commit(self, msg='Sample Commit'):
        self._cmd_git(['commit', '-m', msg, '--allow-empty'])

    def test_commit_details(self):
        self._git_commit('MSG')
        commits = list(self.git_miner.traverse_commits_back())
        self.assertEqual(len(commits), 1)
        c = commits[0]
        self.assertEqual(c.title, 'MSG')
        self.assertEqual(c.author, f"{self.git_user_name} <{self.git_user_email}>")
        self.assertEqual(c.committer, f"{self.git_user_name} <{self.git_user_email}>")
        self.assertIsInstance(c.author_date, datetime)
        self.assertIsInstance(c.commit_date, datetime)
        self.assertEqual(len(c.sha), 40)

    def test_commits_should_be_in_order(self):
        self._git_commit('1')
        self._git_commit('2')
        self._git_commit('3')
        commits = list(self.git_miner.traverse_commits_back())
        self.assertEqual(len(commits), 3)
        self.assertEqual(commits[0].title, '3')
        self.assertEqual(commits[1].title, '2')
        self.assertEqual(commits[2].title, '1')

class GitMinerFactoryTest(TestCase):
    def setUp(self) -> None:
        self.repo_orig_path = tempfile.mkdtemp()
        self._cmd_git(['init'])
        self.git_user_email = 'test@test.com'
        self.git_user_name = 'test user'
        self._cmd_git(['config', 'user.email', self.git_user_email])
        self._cmd_git(['config', 'user.name', self.git_user_name])
        self._cmd_git(['commit', '-m', 'sample', '--allow-empty'])

    def tearDown(self) -> None:
        shutil.rmtree(self.repo_orig_path)

    def _cmd_git(self, cmd: List[str]):
        os_utils.run_cmd(['git'] + cmd, cwd=self.repo_orig_path, raise_on_non_zero_code=True)

    def test_temp_directory_should_be_cleared(self):
        miner_resource = GitMinerFactory.from_url(f"file:///{self.repo_orig_path}")
        tmp_dir = None
        with miner_resource as miner:
            tmp_dir = miner_resource.repo_path
            self.assertIsNotNone(tmp_dir)
            self.assertTrue(os.path.isdir(f"{tmp_dir}/.git/"))
        self.assertFalse(os.path.isdir(tmp_dir))

    def test_temp_directory_should_be_cleared_on_enter_exception(self):
        miner_resource = GitMinerFactory.from_url(f"problematic_url")
        with self.assertRaises(Exception):
            with miner_resource:
                pass
        tmp_dir = miner_resource.repo_path
        self.assertIsNotNone(tmp_dir)
        self.assertFalse(os.path.isdir(tmp_dir))
