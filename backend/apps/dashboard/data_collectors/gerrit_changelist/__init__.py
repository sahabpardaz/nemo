from typing import Iterable
from celery.utils.log import get_task_logger
from rest_framework import serializers
from apps.devops_metrics.serializers import ChangeListSerializer
from apps.utils import exception_utils
from apps.utils.git_miner import GitCommandException, GitMinerFactory, Commit
from apps.devops_metrics.models import ChangeList
from apps.dashboard.models import GitRepo
from apps.dashboard.data_collectors.base import DataCollector
from apps.dashboard.data_collectors.registry import register
from apps.utils.trace_utils import ElapsedTimeTracer

logger = get_task_logger(__name__)
elapsed_time_tracer = ElapsedTimeTracer(logger)


@register()
class GerritChangeListCollector(DataCollector):
    GERRIT_CHANGE_ID_TITLE = 'Change-Id:'

    class ChangeListIdNotFoundException(Exception):
        def __init__(self, commit_sha, commit_body):
            super()\
                .__init__(f'''\
Could not find the "{GerritChangeListCollector.GERRIT_CHANGE_ID_TITLE}" in the commit message body.
Commit sha: {commit_sha}
Commit Body:
{commit_body}''')

    def collect_and_save_data(self):
        logger.info("Gerrit data collection started!")
        git_repos = GitRepo.objects\
            .filter(changelist_collection_enabled=True)\
            .filter(git_ecosystem=GitRepo.GIT_ECOSYSTEM_GERRIT)
        for git_repo in git_repos:
            try:
                self.save_new_changelists_of_repo(git_repo)
            except GitCommandException as e:
                logger.exception(e)
            except serializers.ValidationError:
                logger.exception(f'Failed to validate and save project ({git_repo.nemo_project}) changelists.')

    def save_new_changelists_of_repo(self, git_repo: GitRepo):
        elapsed_time_tracer.reset(f"Started collecting new changelists ... (GitRepo ID: {git_repo.pk})")
        new_changelists = self.get_new_changelists(git_repo)
        elapsed_time_tracer.log("New Nemo changelists created.")
        for cl in new_changelists:
            try:
                ChangeListSerializer.validate_and_save(instance=cl,
                                                       context={'project_id': cl.project_id})
            except Exception as e:
                if not exception_utils.is_exception_about_unique_constraint(e):
                    raise e
        elapsed_time_tracer.log("New changelists saved.")

    def get_new_changelists(self, git_repo: GitRepo):
        # TODO: Find the latest changelist based on the previous data collection, instead of depending on the id.
        # Issue #15175
        latest_changelist = ChangeList.objects.filter(project_id=git_repo.nemo_project_id)\
            .order_by('id').last()
        with GitMinerFactory.from_url(git_repo.git_http_url,
                                      git_repo.default_branch,
                                      git_repo.username,
                                      git_repo.password) as miner:
            commits_generator = miner.traverse_commits_back()
            elapsed_time_tracer.log("Got commits generator object.")
            new_commits = [c for c in self._get_new_commits(latest_changelist, commits_generator) if not c.is_merge]
            elapsed_time_tracer.log(f"Found {len(new_commits)} new commits.")
        new_commits.reverse()
        new_changelists = []
        for c in new_commits:
            try:
                new_changelists.append(ChangeList(project_id=git_repo.nemo_project_id,
                                                  title=c.title,
                                                  commit_hash=c.sha,
                                                  time=self._get_commit_merge_time(c),
                                                  change_list_id=self._get_changelist_id(c)
                                                  ))
            except GerritChangeListCollector.ChangeListIdNotFoundException as e:
                # TODO: Report this misbehavior of a gerrit project as a project configuration warning
                # See issue #11365 for more details.
                logger.info('Could not find Change-Id in commit message.\n'
                            f'Project: {git_repo.nemo_project}\n'
                            f'Commit: {c.sha}')
        return new_changelists

    def _get_new_commits(self, latest_changelist: ChangeList, commits: Iterable[Commit]) -> Iterable[Commit]:
        for c in commits:
            if latest_changelist is not None and c.sha == latest_changelist.commit_hash:
                break
            yield c

    def _get_changelist_id(self, commit: Commit) -> str:
        if GerritChangeListCollector.GERRIT_CHANGE_ID_TITLE not in commit.body:
            raise GerritChangeListCollector.ChangeListIdNotFoundException(commit.sha, commit.body)
        parts = commit.body.split(GerritChangeListCollector.GERRIT_CHANGE_ID_TITLE)
        changelist_id = parts[-1].partition('\n')[0].strip()
        return changelist_id

    def _get_commit_merge_time(self, commit: Commit):
        return commit.commit_date
