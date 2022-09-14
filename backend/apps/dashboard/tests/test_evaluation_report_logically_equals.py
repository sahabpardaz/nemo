from django.test.testcases import TestCase
from apps.dashboard.tests.utils import setup_basic_environment
from apps.dashboard.models import MaturityModelItem, EvaluationReport, EvaluationType


class EvaluationReportLogicallyEqualsTest(TestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()
        evaluation_type = EvaluationType.objects.create(kind=EvaluationType.KIND_MANUAL)
        self.mm_item = MaturityModelItem.objects.create(
            name='Manual',
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )

    def test_logically_equals_ignores_types_of_current_and_expected_value_fields(self):
        """
        Unsaved model instances can have integer instead of string in their char fields
        but saved model instances have only strings.
        """
        current_value = 0
        expected_value = 0
        saved_evaluation_report = EvaluationReport.create_new(
            project=self.env.project,
            maturity_model_item=self.mm_item,
            status=EvaluationReport.STATUS_PASS,
            current_value=current_value,
            expected_value=expected_value,
        )
        saved_evaluation_report.save()
        saved_evaluation_report.refresh_from_db()
        unsaved_evaluation_report = EvaluationReport.create_new(
            project=self.env.project,
            maturity_model_item=self.mm_item,
            status=EvaluationReport.STATUS_PASS,
            current_value=current_value,
            expected_value=expected_value,
        )
        self.assertTrue(saved_evaluation_report.logically_equals(unsaved_evaluation_report))
