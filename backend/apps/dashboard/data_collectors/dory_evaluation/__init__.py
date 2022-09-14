import json
import logging
from typing import List, Optional
import requests
from requests import codes
from requests.exceptions import HTTPError
from django.conf import settings
from django.utils import timezone
from apps.dashboard.models import (
    GitRepo,
    DoryEvaluation,
    Project,
)
from apps.dashboard.models.dory import MaturityItemDoryResult
from apps.utils.url import get_authorized_url
from apps.dashboard.data_collectors.base import DataCollector
from apps.dashboard.data_collectors.registry import register

logger = logging.getLogger(__name__)


@register()
class DoryEvaluationCollector(DataCollector):
    class ItemResultsNotReady(Exception):
        pass

    class InvalidResponseCode(HTTPError):
        pass

    class DoryEvaluationIsRemoved(Exception):
        pass

    class DoryRuntimeError(Exception):
        pass

    def collect_and_save_data(self):
        for project in Project.objects.all():
            self.collect_and_save_dory_evaluation(project)

    def collect_and_save_dory_evaluation(self, project):
        try:
            git_repo = GitRepo.objects.get(nemo_project=project)
        except GitRepo.DoesNotExist:
            logger.warning(f"Project {project.name} has not completed git repo settings in order to be evaluated with dory.")
            return

        latest_non_completed_evaluation = DoryEvaluation.get_latest_non_completed_evaluation(project)
        if not latest_non_completed_evaluation:
            dory_evaluation_submission_id = self.request_to_evaluate(git_repo)
            DoryEvaluation.objects.create(
                project=project,
                submission_id=dory_evaluation_submission_id,
            )
            return

        is_dory_evaluation_completed = True
        try:
            maturity_item_dory_results = self.get_maturity_item_dory_results(
                dory_evaluation_submission_id=latest_non_completed_evaluation.submission_id,
            )
        except DoryEvaluationCollector.ItemResultsNotReady as e:
            logger.info(e, exc_info=True)
            is_dory_evaluation_completed = False
            return
        except (DoryEvaluationCollector.DoryEvaluationIsRemoved, DoryEvaluationCollector.DoryRuntimeError) as e:
            logger.warning(e, exc_info=True)
            return
        finally:
            if is_dory_evaluation_completed and latest_non_completed_evaluation.first_completed_poll_time is None:
                latest_non_completed_evaluation.first_completed_poll_time = timezone.now()
                latest_non_completed_evaluation.save()

        if not maturity_item_dory_results:
            return

        latest_non_completed_evaluation.set_maturity_item_dory_results(maturity_item_dory_results)
        latest_non_completed_evaluation.save()

    def request_to_evaluate(self, git_repo: GitRepo) -> str:
        """
        Raises:
            DoryEvaluationCollector.InvalidResponseCode: If Dory returns an unexpected HTTP status code

        Returns:
            str: Dory evaluation ID
        """
        response = requests.post(
            self.get_evaluations_url(),
            json={
                "repository_url": get_authorized_url(git_repo.git_http_url, git_repo.username, git_repo.password),
                "branch": git_repo.default_branch,
            },
        )
        if response.status_code != codes.accepted:
            raise DoryEvaluationCollector.InvalidResponseCode(
                f"Unexpected status code for submiting evaluation request to dory."
                f"(status_code: {response.status_code}, response_body: {response.text})"
            )

        return json.loads(response.text)['id']

    def get_maturity_item_dory_results(self, dory_evaluation_submission_id: str) -> List[MaturityItemDoryResult]:
        """
        Raises:
            DoryEvaluationCollector.InvalidResponseCode: If Dory returns an unexpected HTTP status code
            DoryEvaluationCollector.ItemResultsNotReady: If Dory still evaluating the project and results are not ready
            DoryEvaluationCollector.DoryEvaluationIsRemoved: If the evaluation with given ID has been removed from Dory
            DoryRuntimeError: If the evaluation in Dory faced an error.

        Returns:
            List[MaturityItemDoryResult]: Full item results
        """
        response = requests.get(self.get_evaluations_url(dory_evaluation_submission_id))
        if response.status_code == codes.ok:
            response_json = json.loads(response.text)
            dory_evaluation_run_error = response_json['run_error']
            if dory_evaluation_run_error:
                raise DoryEvaluationCollector.DoryRuntimeError(f"Some errors happened in dory server: {dory_evaluation_run_error}")

            return [MaturityItemDoryResult(**item_result) for item_result in response_json['item_results']]

        elif response.status_code == codes.accepted:
            raise DoryEvaluationCollector.ItemResultsNotReady(
                f"Dory evaluation with id {dory_evaluation_submission_id} is not completed yet."
            )
        elif response.status_code == codes.not_found:
            raise DoryEvaluationCollector.DoryEvaluationIsRemoved(
                f"Dory evaluation with id {dory_evaluation_submission_id} no found."
            )
        else:
            raise DoryEvaluationCollector.InvalidResponseCode(
                f"Unexpected status code for fetching evaluation results from dory. (status_code: {response.status_code})"
            )

    @staticmethod
    def get_evaluations_url(id: str = None) -> str:
        return f"{settings.DORY_API_URL}/evaluations/{id if id else ''}"
