import dataclasses
import json
from typing import List
import mock
from django.test import TestCase
from rest_framework import status
from apps.dashboard.data_collectors.dory_evaluation import DoryEvaluationCollector
from apps.dashboard.tests.utils import setup_basic_environment
from apps.dashboard.models import (
    EvaluationType,
    DoryEvaluation,
    MaturityModelItem,
    GitRepo,
)
from apps.dashboard.models.dory import MaturityItemDoryResult


class DorySubmissionMock:

    def __init__(self, results: List[MaturityItemDoryResult], run_error: str = None) -> None:
        self.submission_id = "1f57363a-72ab-4c15-b931-008ba6384275"
        self.dory_results = results
        self.run_error = run_error

    def __enter__(self):
        self._request_get_patch = mock.patch('requests.get')
        mock_get = self._request_get_patch.__enter__()
        mock_get.return_value.text = self._get_get_response_text()
        mock_get.return_value.status_code = status.HTTP_200_OK

        self._request_post_patch = mock.patch('requests.post')
        mock_post = self._request_post_patch.__enter__()
        mock_post.return_value.text = self._get_post_response_text()
        mock_post.return_value.status_code = status.HTTP_202_ACCEPTED

        return self.submission_id

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._request_get_patch.__exit__(exc_type, exc_value, exc_tb)
        self._request_post_patch.__exit__(exc_type, exc_value, exc_tb)

    def _get_post_response_text(self):
        return json.dumps({
            'id': self.submission_id
        })

    def _get_get_response_text(self):
        return json.dumps({
            'id': self.submission_id,
            'run_error': self.run_error,
            'item_results': [dataclasses.asdict(r) for r in self.dory_results]
        })


class DoryEvaluationCollectorTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        GitRepo.objects.create(
            nemo_project=self.env.project,
            git_http_url="http://test.test/project.git",
            git_ecosystem=GitRepo.GIT_ECOSYSTEM_OTHER,
        )
        self.dory_evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_DORY,
        )

    def test_submitting_project_with_two_dory_items_should_return_two_item_results(self):
        mm_items = [
            MaturityModelItem.objects.create(
                code="D001",
                name="Dory 1",
                evaluation_type=self.dory_evaluation_type,
                maturity_model_level=self.env.maturity_model_level,
            ),
            MaturityModelItem.objects.create(
                code="D002",
                name="Dory 2",
                evaluation_type=self.dory_evaluation_type,
                maturity_model_level=self.env.maturity_model_level,
            ),
        ]

        with DorySubmissionMock([
            MaturityItemDoryResult(mm_items[0].code, True, "Oh yes"),
            MaturityItemDoryResult(mm_items[1].code, False, "Oh no"),
        ]):
            DoryEvaluationCollector().collect_and_save_data()
            DoryEvaluationCollector().collect_and_save_data()

            self.assertEquals(
                DoryEvaluation.objects.count(), 1,
                msg="DoryEvaluator should not create any DoryEvaluation when a new one is already sent.",
            )
            with DoryEvaluation.objects.first().maturity_item_dory_results_file.open('r') as f:
                item_results = f.read()
            self.assertEquals(len(json.loads(item_results)), 2)

    def test_first_completed_poll_time_field_should_be_set_after_first_poll(self):
        MaturityModelItem.objects.create(
            code="D001",
            name="Dory 1",
            evaluation_type=self.dory_evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )

        with DorySubmissionMock([MaturityItemDoryResult("D002", True, "Oh yes")]):
            DoryEvaluationCollector().collect_and_save_data()
            assert DoryEvaluation.objects.count() == 1
            self.assertIsNone(DoryEvaluation.objects.first().first_completed_poll_time)

            DoryEvaluationCollector().collect_and_save_data()
            assert DoryEvaluation.objects.count() == 1
            self.assertIsNotNone(DoryEvaluation.objects.first().first_completed_poll_time)
