from datetime import timedelta, datetime
from django.test import TestCase
from django.utils import timezone
from apps.dashboard.models import EvaluationType, MaturityModelItem, EvaluationReport
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment
from apps.dashboard.project_retrieve_utils import (
    LatestEvaluationReportFinder,
    get_maturity_model_item_status,
    FAIL_STATUS,
    PASS_STATUS,
    ITEM_FAIL_REASON_NO_EVALUATION_REPORT_FOUND,
    ITEM_FAIL_REASON_OUT_OF_VALIDITY_PERIOD,
    ITEM_FAIL_REASON_LAST_EVALUATION_FAILED,
)


class ItemStatusTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        self.VALIDITY_PERIOD_DAYS = 10
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
            validity_period_days=self.VALIDITY_PERIOD_DAYS,
            checking_period_days=0,
        )
        self.mm_item = MaturityModelItem.objects.create(
            name='Manual',
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        self.now = timezone.make_aware(datetime(2000, 1, 1))
        self.latest_evaluation_report_finder = LatestEvaluationReportFinder(
            project=self.env.project,
            current_time=self.now,
            evaluation_reports_extra_fields=['current_value', 'expected_value', 'value_type'],
        )

    def test_item_must_be_failed_if_no_evaluation_report_exists(self):
        self.assertEqual(
            get_maturity_model_item_status(
                maturity_model_item=self.mm_item,
                latest_evaluation_report=self._get_latest_evaluation_report(self.mm_item),
                current_time=self.now,
            ),
            (FAIL_STATUS, ITEM_FAIL_REASON_NO_EVALUATION_REPORT_FOUND)
        )

    def test_item_must_be_passed_if_latest_evaluation_report_passed_and_is_in_validity_period(self):
        self._create_evaluation_report(EvaluationReport.STATUS_PASS)
        self.assertEqual(
            get_maturity_model_item_status(
                maturity_model_item=self.mm_item,
                latest_evaluation_report=self._get_latest_evaluation_report(self.mm_item),
                current_time=self.now,
            ),
            (PASS_STATUS, None)
        )

    def test_item_must_be_failed_if_latest_evaluation_report_passed_and_is_after_validity_period(self):
        self._create_evaluation_report(EvaluationReport.STATUS_PASS)
        self.assertEqual(
            get_maturity_model_item_status(
                maturity_model_item=self.mm_item,
                latest_evaluation_report=self._get_latest_evaluation_report(self.mm_item),
                current_time=self.now + timedelta(days=self.VALIDITY_PERIOD_DAYS + 2),
            ),
            (FAIL_STATUS, ITEM_FAIL_REASON_OUT_OF_VALIDITY_PERIOD)
        )

    def test_item_must_be_failed_with_evaluation_failed_reason_if_latest_evaluation_report_failed_and_is_after_validity_period(self):
        self._create_evaluation_report(EvaluationReport.STATUS_FAIL)
        self.assertEqual(
            get_maturity_model_item_status(
                maturity_model_item=self.mm_item,
                latest_evaluation_report=self._get_latest_evaluation_report(self.mm_item),
                current_time=self.now + timedelta(days=self.VALIDITY_PERIOD_DAYS + 2),
            ),
            (FAIL_STATUS, ITEM_FAIL_REASON_LAST_EVALUATION_FAILED)
        )

    def test_item_must_be_failed_if_latest_evaluation_report_failed(self):
        self._create_evaluation_report(EvaluationReport.STATUS_FAIL)
        self.assertEqual(
            get_maturity_model_item_status(
                maturity_model_item=self.mm_item,
                latest_evaluation_report=self._get_latest_evaluation_report(self.mm_item),
                current_time=self.now,
            ),
            (FAIL_STATUS, ITEM_FAIL_REASON_LAST_EVALUATION_FAILED)
        )

    def test_item_should_be_passed_when_latest_evaluation_report_passed_and_current_time_is_between_creation_time_and_latest_evaluation_time(self):
        evaluation_report = self._create_evaluation_report(EvaluationReport.STATUS_PASS)
        evaluation_report.latest_evaluation_time = self.now + timedelta(days=2)
        evaluation_report.save()
        self.assertEqual(
            get_maturity_model_item_status(
                maturity_model_item=self.mm_item,
                latest_evaluation_report=self._get_latest_evaluation_report(self.mm_item),
                current_time=self.now + timedelta(days=1),
            ),
            (PASS_STATUS, None)
        )

    def _create_evaluation_report(self, status):
        with DjangoCurrentTimeMock(self.now):
            return EvaluationReport.objects.create(
                maturity_model_item=self.mm_item,
                project=self.env.project,
                status=status,
            )

    def _get_latest_evaluation_report(self, maturity_model_item: MaturityModelItem):
        return self.latest_evaluation_report_finder.get_latest_evaluation_report_of_item(maturity_model_item.id)
