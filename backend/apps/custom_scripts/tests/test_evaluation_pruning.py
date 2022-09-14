from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from apps.dashboard.models import EvaluationType, MaturityModelItem, EvaluationReport, EvaluationRequest
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment
from apps.custom_scripts.evaluation_report_pruning import remove_repeater_evaluation_reports


class Test(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()

    def test_burst_logically_equal_evaluation_reports_of_non_manual_items_should_be_reduced_to_one(self):
        evaluation_type_non_manual = EvaluationType.objects.create(
            kind=EvaluationType.KIND_TEST_COVERAGE,  # Arbitrary non-manual type
            validity_period_days=1,
        )
        self.mm_item_non_manual = MaturityModelItem.objects.create(
            code="N000",
            name="Test Coverage",
            evaluation_type=evaluation_type_non_manual,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value="50"
        )
        non_manual_evaluation_reports = [
            self._create_non_manual_evaluation_report(60),
            self._create_non_manual_evaluation_report(60),
            self._create_non_manual_evaluation_report(70),
        ]

        remove_repeater_evaluation_reports()

        self.assertEqual(EvaluationReport.objects.filter(maturity_model_item=self.mm_item_non_manual).count(), 2)
        first_non_manual_evaluation_report = EvaluationReport.objects.order_by('creation_time').first()
        self.assertEqual(first_non_manual_evaluation_report.creation_time, non_manual_evaluation_reports[0].creation_time)
        self.assertEqual(first_non_manual_evaluation_report.latest_evaluation_time, non_manual_evaluation_reports[1].latest_evaluation_time)

    def test_evaluation_reports_of_manual_items_should_not_be_deleted(self):
        evaluation_type_manual = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
        )
        self.mm_item_manual = MaturityModelItem.objects.create(
            code="M000",
            name="Manual",
            evaluation_type=evaluation_type_manual,
            maturity_model_level=self.env.maturity_model_level,
        )
        self._create_manual_evaluation_request_and_report("test 1")
        self._create_manual_evaluation_request_and_report("test 1")
        self._create_manual_evaluation_request_and_report("test 2")

        remove_repeater_evaluation_reports()

        self.assertEqual(EvaluationReport.objects.filter(maturity_model_item=self.mm_item_manual).count(), 3)

    def test_evaluation_report_should_not_be_merged_with_previous_evaluation_report_that_is_not_in_validity_period(self):
        validity_period_days = 1
        evaluation_type_non_manual = EvaluationType.objects.create(
            kind=EvaluationType.KIND_TEST_COVERAGE,  # Arbitrary non-manual type
            validity_period_days=validity_period_days,
        )
        self.mm_item_non_manual = MaturityModelItem.objects.create(
            code="N000",
            name="Test Coverage",
            evaluation_type=evaluation_type_non_manual,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value="50"
        )
        now = timezone.make_aware(datetime(2000, 1, 1))
        with DjangoCurrentTimeMock(now):
            self._create_non_manual_evaluation_report(current_value="60")

        with DjangoCurrentTimeMock(now + timedelta(days=validity_period_days + 1)):
            self._create_non_manual_evaluation_report(current_value="60")

        remove_repeater_evaluation_reports()

        self.assertEqual(EvaluationReport.objects.filter(maturity_model_item=self.mm_item_non_manual).count(), 2)

    def _create_non_manual_evaluation_report(self, current_value):
        evaluation_report = EvaluationReport.create_new(
            project=self.env.project,
            maturity_model_item=self.mm_item_non_manual,
            status=EvaluationReport.STATUS_PASS,
            current_value=current_value,
        )
        evaluation_report.save()
        evaluation_report.refresh_from_db()
        return evaluation_report

    def _create_manual_evaluation_request_and_report(self, description):
        EvaluationRequest.objects.create(
            project=self.env.project,
            maturity_model_item=self.mm_item_manual,
            applicant=self.env.user,
        )
        EvaluationReport.create_new(
            project=self.env.project,
            maturity_model_item=self.mm_item_manual,
            status=EvaluationReport.STATUS_PASS,
            description=description,
        ).save()
