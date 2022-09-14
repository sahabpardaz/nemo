from datetime import datetime, timedelta
from typing import List
import mock
from django.test import TestCase
from django.utils import timezone
from apps.dashboard.evaluators.dory_evaluator import (
    DoryEvaluator,
    DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriod,
    DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriod,
)
from apps.dashboard.models.dory import MaturityItemDoryResult
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment
from apps.dashboard.models import (
    EvaluationType,
    DoryEvaluation,
    MaturityModelItem,
    EvaluationReport,
)


class DoryEvaluatorBaseTestCase(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        self.dory_evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_DORY,
            checking_period_days=10,
        )
        self.now = timezone.make_aware(datetime(2000, 1, 1))

    def _create_fake_dory_evaluation(self, maturity_item_dory_results: List[MaturityItemDoryResult]):
        dory_evaluation = DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="1",
            submission_time=self.now - timedelta(days=2),
            first_completed_poll_time=self.now - timedelta(days=1),
        )
        dory_evaluation.set_maturity_item_dory_results(maturity_item_dory_results)
        dory_evaluation.save()
        return dory_evaluation


class DoryEvaluatorTest(DoryEvaluatorBaseTestCase):
    def test_DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriod_should_be_used_when_maturity_item_acceptable_value_is_none(self):
        mm_item = MaturityModelItem.objects.create(
            code="D001",
            name="Dory 1",
            evaluation_type=self.dory_evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        with mock.patch.object(DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriod, 'evaluate') as mocked:
            DoryEvaluator().evaluate(self.env.project, mm_item)
            mocked.assert_called()


class DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriodTest(DoryEvaluatorBaseTestCase):
    def test_no_report_should_be_created_when_there_is_no_dory_evaluation(self):
        mm_item = MaturityModelItem.objects.create(
            code="D001",
            name="Dory 1",
            evaluation_type=self.dory_evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        with DjangoCurrentTimeMock(self.now):
            evaluation_report = DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriod().evaluate(self.env.project, mm_item)
        self.assertIsNone(evaluation_report)

    def test_evaluating_item_that_has_no_nemo_yml_specification_should_not_generate_report(self):
        mm_item = MaturityModelItem.objects.create(
            code="D001",
            name="Dory 1",
            evaluation_type=self.dory_evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        self._create_fake_dory_evaluation(maturity_item_dory_results=[])
        with DjangoCurrentTimeMock(self.now):
            generated_evaluation_report = DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriod().evaluate(self.env.project, mm_item)
        self.assertIsNone(generated_evaluation_report)

    def test_evaluating_two_dory_items_with_defined_script_should_return_two_evaluation_reports(self):
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
        self._create_fake_dory_evaluation(maturity_item_dory_results=[
            MaturityItemDoryResult(mm_items[0].code, True, "Oh yes"),
            MaturityItemDoryResult(mm_items[1].code, False, "Oh no"),
        ])
        with DjangoCurrentTimeMock(self.now):
            generated_evaluation_report_1 = DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriod().evaluate(self.env.project, mm_items[0])
            generated_evaluation_report_2 = DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriod().evaluate(self.env.project, mm_items[1])

        self.assertIsNotNone(generated_evaluation_report_1)
        self.assertIsNotNone(generated_evaluation_report_2)


class DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriodTest(DoryEvaluatorBaseTestCase):
    def test_no_report_should_be_created_when_there_is_no_dory_evaluation(self):
        mm_item = MaturityModelItem.objects.create(
            code="D001",
            name="Dory 1",
            evaluation_type=self.dory_evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value=100.0,
            acceptable_value_type=MaturityModelItem.VALUE_TYPE_PERCENTAGE,
        )
        with DjangoCurrentTimeMock(self.now):
            evaluation_report = DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriod().evaluate(self.env.project, mm_item)
        self.assertIsNone(evaluation_report)

    def test_evaluating_item_that_has_no_nemo_yml_specification_should_not_generate_report(self):
        mm_item = MaturityModelItem.objects.create(
            code="D001",
            name="Dory 1",
            evaluation_type=self.dory_evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value=100.0,
            acceptable_value_type=MaturityModelItem.VALUE_TYPE_PERCENTAGE,
        )
        self._create_fake_dory_evaluation(maturity_item_dory_results=[])
        with DjangoCurrentTimeMock(self.now):
            generated_evaluation_report = DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriod().evaluate(self.env.project, mm_item)
        self.assertIsNone(generated_evaluation_report)

    def test_evaluating_two_dory_items_with_defined_script_should_return_two_evaluation_reports(self):
        mm_items = [
            MaturityModelItem.objects.create(
                code="D001",
                name="Dory 1",
                evaluation_type=self.dory_evaluation_type,
                maturity_model_level=self.env.maturity_model_level,
                acceptable_value=100.0,
                acceptable_value_type=MaturityModelItem.VALUE_TYPE_PERCENTAGE,
            ),
            MaturityModelItem.objects.create(
                code="D002",
                name="Dory 2",
                evaluation_type=self.dory_evaluation_type,
                maturity_model_level=self.env.maturity_model_level,
                acceptable_value=100.0,
                acceptable_value_type=MaturityModelItem.VALUE_TYPE_PERCENTAGE,
            ),
        ]
        self._create_fake_dory_evaluation(maturity_item_dory_results=[
            MaturityItemDoryResult(mm_items[0].code, True, "Oh yes"),
            MaturityItemDoryResult(mm_items[1].code, False, "Oh no"),
        ])
        with DjangoCurrentTimeMock(self.now):
            generated_evaluation_report_1 = DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriod().evaluate(self.env.project, mm_items[0])
            generated_evaluation_report_2 = DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriod().evaluate(self.env.project, mm_items[1])

        self.assertIsNotNone(generated_evaluation_report_1)
        self.assertIsNotNone(generated_evaluation_report_2)

    def test_evaluation_report_should_be_fail_when_current_value_is_lower_than_expected_value(self):
        mm_item = MaturityModelItem.objects.create(
            code="D001",
            name="Dory 1",
            evaluation_type=self.dory_evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value=50.0,
            acceptable_value_type=MaturityModelItem.VALUE_TYPE_PERCENTAGE,
        )
        for maturity_item_dory_result in [
            MaturityItemDoryResult(mm_item.code, True, "Oh yes"),
            MaturityItemDoryResult(mm_item.code, False, "Oh no 1"),
            MaturityItemDoryResult(mm_item.code, False, "Oh no 2"),
            MaturityItemDoryResult(mm_item.code, False, "Oh no 3"),
        ]:
            self._create_fake_dory_evaluation(maturity_item_dory_results=[maturity_item_dory_result])
        with DjangoCurrentTimeMock(self.now):
            generated_evaluation_report = DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriod().evaluate(self.env.project, mm_item)

        self.assertEquals(generated_evaluation_report.status, EvaluationReport.STATUS_FAIL)
        self.assertEquals(generated_evaluation_report.current_value, str(1/4 * 100))

    def test_evaluation_report_description_should_have_dory_evaluation_ids(self):
        mm_item = MaturityModelItem.objects.create(
            code="D000",
            name="Dory",
            evaluation_type=self.dory_evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value=100.0,
            acceptable_value_type=MaturityModelItem.VALUE_TYPE_PERCENTAGE,
        )
        first_dory_evaluation = self._create_fake_dory_evaluation(maturity_item_dory_results=[MaturityItemDoryResult(mm_item.code, True, "Oh yes")])
        second_dory_evaluation = self._create_fake_dory_evaluation(maturity_item_dory_results=[MaturityItemDoryResult(mm_item.code, True, "Oh yes")])
        with DjangoCurrentTimeMock(self.now):
            generated_evaluation_report = DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriod().evaluate(self.env.project, mm_item)

        self.assertTrue(str(first_dory_evaluation.id) in generated_evaluation_report.description)
        self.assertTrue(str(second_dory_evaluation.id) in generated_evaluation_report.description)
