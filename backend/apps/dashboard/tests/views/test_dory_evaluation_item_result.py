from rest_framework import status
from rest_framework.test import APITestCase
from apps.dashboard.models import DoryEvaluation
from apps.dashboard.models.dory import MaturityItemDoryResult
from apps.dashboard.tests.utils import setup_basic_environment


class DoryEvaluationViewSetMaturityItemDoryResultEndPointTest(APITestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        self.client.force_login(self.env.user)

    def test_endpoint_should_return_404_when_dory_evaluation_not_found(self):
        response = self._get_item_result_response(dory_evaluation_id=1, item_code="1")
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_endpoint_should_return_404_when_maturity_item_dory_results_file_not_exists(self):
        dory_evaluation = DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="TEST",
        )
        response = self._get_item_result_response(dory_evaluation_id=dory_evaluation.id, item_code="1")
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_endpoint_should_return_404_when_item_code_not_found_in_maturity_item_results(self):
        item_code = "CODE"
        dory_evaluation = DoryEvaluation(
            project=self.env.project,
            submission_id="TEST",
        )
        dory_evaluation.set_maturity_item_dory_results([MaturityItemDoryResult(item_code, True, "description")])
        dory_evaluation.save()
        response = self._get_item_result_response(dory_evaluation_id=dory_evaluation.id, item_code="NONE")
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_endpoint_should_return_200_when_everything_is_ok(self):
        item_code = "CODE"
        dory_evaluation = DoryEvaluation(
            project=self.env.project,
            submission_id="TEST",
        )
        dory_evaluation.set_maturity_item_dory_results([MaturityItemDoryResult(item_code, True, "description")])
        dory_evaluation.save()
        response = self._get_item_result_response(dory_evaluation_id=dory_evaluation.id, item_code=item_code)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def _get_item_result_response(self, dory_evaluation_id, item_code):
        return self.client.get(f'/v1/dashboard/project/{self.env.project.id}/dory-evaluation/{dory_evaluation_id}/maturity-item-result/{item_code}/')
