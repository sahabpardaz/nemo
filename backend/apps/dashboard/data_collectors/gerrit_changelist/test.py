
from datetime import datetime, timedelta
import tempfile
from typing import List
import shutil
from django.test import TestCase
from apps.dashboard.data_collectors.gerrit_changelist import GerritChangeListCollector
from apps.dashboard.models.project import GitRepo
from apps.devops_metrics.models import ChangeList
from apps.utils import os_utils

from apps.dashboard.tests.utils import setup_basic_environment
from apps.utils.git_miner.git_command_exception import GitCommandException
from apps.utils.validation_utils import InconsistentDataError


class GerritChangeListCollectorTest(TestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()
        ChangeList.objects.all().delete()
        self.next_valid_change_id = 1
        self.changelist_collector = GerritChangeListCollector()
        self.repo_path = tempfile.mkdtemp()
        self._cmd_git(['init'])
        self.git_user_email = 'test@test.com'
        self.git_user_name = 'test user'
        self._cmd_git(['config', 'user.email', self.git_user_email])
        self._cmd_git(['config', 'user.name', self.git_user_name])
        self.nemo_git_repo = GitRepo(nemo_project=self.env.project,
                                     git_http_url=f'file:///{self.repo_path}',
                                     default_branch="master",
                                     git_ecosystem=GitRepo.GIT_ECOSYSTEM_GERRIT,
                                     changelist_collection_enabled=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.repo_path)

    def _generate_change_id(self):
        id = self.next_valid_change_id
        self.next_valid_change_id += 1
        return id

    def _cmd_git(self, cmd: List[str], commit_date: datetime = None):
        env = {}
        if commit_date is not None:
            env = {
                'GIT_COMMITTER_DATE': str(commit_date)
            }
        return os_utils.run_cmd(['git'] + cmd, cwd=self.repo_path, raise_on_non_zero_code=True, additional_env=env)

    def _git_commit(self, msg="Sample Commit", commit_date: datetime = None):
        return self._cmd_git(['commit', '-m', msg, '--allow-empty'], commit_date)

    def _gerrit_commit(self, msg="Sample Commit", commit_date: datetime = None, change_id: str = None):
        if change_id is None:
            change_id = self._generate_change_id()
        return self._git_commit(f"{msg}\n\n    Change-Id: {change_id}", commit_date)

    def test_no_changelist_should_create_when_no_commit_exists(self):
        with self.assertRaises(GitCommandException):
            self.changelist_collector.get_new_changelists(self.nemo_git_repo)

    def test_commits_should_be_detected_for_the_first_time(self):
        self._gerrit_commit()
        new_changelists = self.changelist_collector.get_new_changelists(self.nemo_git_repo)
        self.assertEqual(len(new_changelists), 1)

    def test_commits_without_change_id_should_be_ignored(self):
        self._git_commit(msg="Sample Commit Without C h a n g e - I d")
        new_changelists = self.changelist_collector.get_new_changelists(self.nemo_git_repo)
        self.assertEqual(len(new_changelists), 0)

    def test_old_commit_should_not_be_detected(self):
        self._gerrit_commit()
        self.changelist_collector.save_new_changelists_of_repo(self.nemo_git_repo)
        new_changelists = self.changelist_collector.get_new_changelists(self.nemo_git_repo)
        self.assertEqual(len(new_changelists), 0)

    def test_new_commits_should_be_detected(self):
        self._gerrit_commit('1')
        self.changelist_collector.save_new_changelists_of_repo(self.nemo_git_repo)
        self._gerrit_commit('2')
        new_changelists = self.changelist_collector.get_new_changelists(self.nemo_git_repo)
        self.assertEqual(len(new_changelists), 1)
        self.assertEqual(new_changelists[0].title, '2')

    def test_changelists_should_save_in_commit_order(self):
        self._gerrit_commit('1')
        self._gerrit_commit('2')
        self._gerrit_commit('3')
        self.changelist_collector.save_new_changelists_of_repo(self.nemo_git_repo)
        changelists = list(ChangeList.objects.order_by('id').all())
        self.assertEqual(changelists[0].title, '1')
        self.assertEqual(changelists[1].title, '2')
        self.assertEqual(changelists[2].title, '3')

    def test_changelists_should_save_in_topology_order_even_if_times_are_not_sorted(self):
        first_commit_date = datetime(2010, 1, 1)
        self._gerrit_commit('1', first_commit_date)
        self._gerrit_commit('2', first_commit_date - timedelta(days=1))
        self._gerrit_commit('3', first_commit_date + timedelta(days=1))
        self.changelist_collector.save_new_changelists_of_repo(self.nemo_git_repo)
        changelists = list(ChangeList.objects.order_by('id').all())
        self.assertEqual(changelists[0].title, '1')
        self.assertEqual(changelists[1].title, '2')
        self.assertEqual(changelists[2].title, '3')

    def test_changelist_collection_shouldnt_fail_when_a_newer_cl_already_exists_before_latest_saved_cl(self):
        commit1 = ('1', self._generate_change_id())
        commit2 = ('2', self._generate_change_id())
        commit3 = ('3', self._generate_change_id())
        commit4 = ('4', self._generate_change_id())
        commit_hashes = {}
        for title, change_id in [commit1, commit2, commit3, commit4]:
            self._gerrit_commit(msg=title, change_id=change_id)
            result = self._cmd_git(['log','-1', '--format=%H'])
            commit_hashes[title] = result.stdout.decode().rstrip()
        for title, change_id in [commit1, commit3, commit2]:
            ChangeList.objects.create(
                project=self.env.project,
                commit_hash=commit_hashes[title],
                change_list_id=change_id
            )

        self.changelist_collector.save_new_changelists_of_repo(self.nemo_git_repo)

    def test_saving_cl_with_same_change_id_and_different_commit_hash_raises_appropriate_error(self):
        self._gerrit_commit(change_id="1")
        self.changelist_collector.save_new_changelists_of_repo(self.nemo_git_repo)
        self._gerrit_commit(change_id="1")
        with self.assertRaises(InconsistentDataError):
            self.changelist_collector.save_new_changelists_of_repo(self.nemo_git_repo)
