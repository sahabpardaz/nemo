from typing import List
from django.test.testcases import TestCase
from apps.dashboard.tests.utils import setup_basic_environment
from apps.dashboard.models import MaturityModelItem, EvaluationType, DoryEvaluation
from apps.dashboard.models.dory import MaturityItemDoryResult


class DoryEvaluationMaturityItemResultGetterTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        evaluation_type = EvaluationType.objects.create(kind=EvaluationType.KIND_DORY)
        self.mm_item_code = "CODE"
        self.mm_item = MaturityModelItem.objects.create(
            code=self.mm_item_code,
            name='DORY',
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )

    def test_getter_should_return_none_when_maturity_item_dory_results_file_not_filled(self):
        dory_evaluation = self._create_dory_evaluation(maturity_item_dory_results=None)
        self.assertIsNone(
            dory_evaluation.get_maturity_item_dory_result(item_code=self.mm_item_code)
        )

    def test_getter_should_return_none_when_item_code_not_found_in_maturity_item_dory_results_file(self):
        dory_evaluation = self._create_dory_evaluation(
            maturity_item_dory_results=[MaturityItemDoryResult(code="404", passed=True, description="")]
        )
        self.assertIsNone(
            dory_evaluation.get_maturity_item_dory_result(item_code=self.mm_item_code)
        )

    def test_getter_should_return_instance_of_MaturityItemDoryResult_when_item_code_is_in_maturity_item_dory_results_file(self):
        dory_evaluation = self._create_dory_evaluation(
            maturity_item_dory_results=[MaturityItemDoryResult(code=self.mm_item_code, passed=True, description="")]
        )
        self.assertIsInstance(
            dory_evaluation.get_maturity_item_dory_result(item_code=self.mm_item_code),
            MaturityItemDoryResult
        )

    def _create_dory_evaluation(self, maturity_item_dory_results: List[MaturityItemDoryResult]):
        dory_evaluation = DoryEvaluation(
            project=self.env.project,
            submission_id="TEST",
        )
        if maturity_item_dory_results is not None:
            dory_evaluation.set_maturity_item_dory_results(maturity_item_dory_results)
        dory_evaluation.save()
        return dory_evaluation
