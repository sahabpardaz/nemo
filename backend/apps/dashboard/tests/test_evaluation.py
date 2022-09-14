from datetime import datetime, timedelta
import logging
from django.db.utils import IntegrityError
from django.utils import timezone
from rest_framework.test import APITestCase
from apps.dashboard.models.coverage_report import CoverageReport
from apps.dashboard.models import MaturityModelItem, EvaluationReport, EvaluationType
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment
from apps.dashboard.tasks import AutomaticMMItemsEvaluation


logger = logging.getLogger(__name__)

class EvaluationReportTest(APITestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
            validity_period_days=0,
            checking_period_days=0,
        )
        self.mm_item = MaturityModelItem.objects.create(
            name='Manual',
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )

    def test_latest_evaluation_report_by_date_filter(self):
        report_time = timezone.make_aware(datetime(2000, 1, 1, 1, 1, 1, 1))
        EvaluationReport.objects.create(
            project=self.env.project,
            maturity_model_item=self.mm_item,
            status=EvaluationReport.STATUS_PASS,
            creation_time=report_time,
            last_update_time=report_time)
        report_before_report_time = EvaluationReport.get_latest(self.env.project,
                                                                self.mm_item,
                                                                report_time - timedelta(days=1))
        self.assertIsNone(report_before_report_time, "Report should be None according to date filter.")

    def test_latest_evaluation_time_before_creation_time_can_not_be_saved(self):
        current_time = timezone.now()
        evaluation_report = EvaluationReport.objects.create(
            project=self.env.project,
            maturity_model_item=self.mm_item,
            status=EvaluationReport.STATUS_PASS,
        )
        evaluation_report.refresh_from_db()
        with self.assertRaises(IntegrityError):
            evaluation_report.latest_evaluation_time = evaluation_report.creation_time - timedelta(days=1)
            evaluation_report.save()

    def test_only_latest_evaluation_time_of_latest_report_can_be_updated(self):
        evaluation_report = EvaluationReport.objects.create(
            project=self.env.project,
            maturity_model_item=self.mm_item,
            status=EvaluationReport.STATUS_PASS,
        )
        EvaluationReport.objects.create(
            project=self.env.project,
            maturity_model_item=self.mm_item,
            status=EvaluationReport.STATUS_PASS,
        )
        with self.assertRaises(ValueError):
            evaluation_report.latest_evaluation_time = timezone.now()
            evaluation_report.save()


class IsTestCoverageCalculatedEvaluationTest(APITestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()
        self.mm_items_evaluation_task = AutomaticMMItemsEvaluation()
        self.CHECKING_PERIOD_DAYS = 1
        self.VALIDITY_PERIOD_DAYS = 2
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_IS_TEST_COVERAGE_CALCULATED,
            checking_period_days=self.CHECKING_PERIOD_DAYS,
            validity_period_days=self.VALIDITY_PERIOD_DAYS
        )
        self.mm_item = MaturityModelItem.objects.create(
            name="Measure Test Coverage",
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )

    def _create_coverage_report(self, is_recent=True) -> CoverageReport:
        coverage_time = timezone.now()
        if not is_recent:
            coverage_time -= timedelta(days=self.CHECKING_PERIOD_DAYS+1)

        with DjangoCurrentTimeMock(coverage_time):
            return CoverageReport.objects.create(
                project=self.env.project,
                value=0,
                coverage_type=CoverageReport.TYPE_INCREMENTAL,
                creator=self.env.user
            )

    def _create_evaluation_report(self, is_recent=True) -> EvaluationReport:
        evaluation_time = timezone.now()
        if not is_recent:
            evaluation_time -= timedelta(days=self.VALIDITY_PERIOD_DAYS+1)
        with DjangoCurrentTimeMock(evaluation_time):
            evaluation_report = EvaluationReport.create_new(
                maturity_model_item=self.mm_item,
                project=self.env.project,
                reporter=self.env.user,
                status=EvaluationReport.STATUS_PASS
            )
            evaluation_report.save()
            return evaluation_report

    def test_evaluation_should_succeed_when_coverage_reported(self):
        self._create_coverage_report()
        self.mm_items_evaluation_task.run()
        evaluation_report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertIsNotNone(evaluation_report)
        self.assertEqual(evaluation_report.status, EvaluationReport.STATUS_PASS, evaluation_report.description)

    def test_evaluation_should_fail_when_no_coverage_reported(self):
        self.mm_items_evaluation_task.run()
        evaluation_report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertIsNotNone(evaluation_report)
        self.assertEqual(evaluation_report.status, EvaluationReport.STATUS_FAIL, evaluation_report.description)

    def test_evaluation_should_fail_when_coverage_report_is_old(self):
        self._create_coverage_report(is_recent=False)
        self.mm_items_evaluation_task.run()
        evaluation_report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertEqual(evaluation_report.status, EvaluationReport.STATUS_FAIL, evaluation_report.description)

    def test_evaluation_should_succeed_when_recent_succeeded_evaluation_report_exists(self):
        self._create_coverage_report(is_recent=False)
        previous_evaluation_report = self._create_evaluation_report()
        self.mm_items_evaluation_task.run()
        evaluation_report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertEqual(evaluation_report.status, EvaluationReport.STATUS_PASS, evaluation_report.description)
        self.assertEqual(previous_evaluation_report.id, evaluation_report.id, evaluation_report.description)


class OverallTestCoverageEvaluatorTest(APITestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        self.mm_items_evaluation_task = AutomaticMMItemsEvaluation()
        self.CHECKING_PERIOD_DAYS = 1
        self.VALIDITY_PERIOD_DAYS = 2
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_TEST_COVERAGE,
            checking_period_days=self.CHECKING_PERIOD_DAYS,
            validity_period_days=self.VALIDITY_PERIOD_DAYS
        )
        self.mm_item = MaturityModelItem.objects.create(
            name="Test Coverage",
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value="50"
        )

    def test_no_evaluation_should_generate_when_no_coverage_reported(self):
        self.mm_items_evaluation_task.run()
        report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertIsNone(report)

    def test_evaluation_should_pass_when_good_coverage_reported(self):
        CoverageReport.objects.create(
            project=self.env.project,
            value=50.0,
            coverage_type=CoverageReport.TYPE_OVERALL
        )
        self.mm_items_evaluation_task.run()
        report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertEqual(report.status, EvaluationReport.STATUS_PASS)

    def test_evaluation_should_fail_when_less_coverage_reported(self):
        CoverageReport.objects.create(
            project=self.env.project,
            value=35.0,
            coverage_type=CoverageReport.TYPE_OVERALL
        )
        self.mm_items_evaluation_task.run()
        report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertEqual(report.status, EvaluationReport.STATUS_FAIL)
        self.assertEqual(float(report.expected_value), 50.0)
        self.assertEqual(float(report.current_value), 35.0)

    def test_only_latest_coverage_report_should_affect_evaluation(self):
        CoverageReport.objects.create(
            project=self.env.project,
            value=100.0,
            coverage_type=CoverageReport.TYPE_OVERALL
        )
        CoverageReport.objects.create(
            project=self.env.project,
            value=35.0,
            coverage_type=CoverageReport.TYPE_OVERALL
        )
        self.mm_items_evaluation_task.run()
        report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertEqual(report.status, EvaluationReport.STATUS_FAIL)
        self.assertEqual(float(report.current_value), 35.0)

    def test_coverage_report_should_be_in_checking_period(self):
        coverage_time = timezone.now() - timedelta(days=self.CHECKING_PERIOD_DAYS + 1)
        with DjangoCurrentTimeMock(coverage_time):
            CoverageReport.objects.create(
                project=self.env.project,
                value=100.0,
                coverage_type=CoverageReport.TYPE_OVERALL
            )
        self.mm_items_evaluation_task.run()
        report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertIsNone(report)


class IncrementalTestCoverageEvaluatorTest(APITestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        self.mm_items_evaluation_task = AutomaticMMItemsEvaluation()
        self.CHECKING_PERIOD_DAYS = 1
        self.VALIDITY_PERIOD_DAYS = 2
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_INCREMENTAL_TEST_COVERAGE,
            checking_period_days=self.CHECKING_PERIOD_DAYS,
            validity_period_days=self.VALIDITY_PERIOD_DAYS
        )
        self.mm_item = MaturityModelItem.objects.create(
            name="Incremental Test Coverage",
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value="50"
        )

    def test_no_evaluation_should_generate_when_no_coverage_reported(self):
        self.mm_items_evaluation_task.run()
        report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertIsNone(report)

    def test_evalutation_should_pass_when_good_coverage_reported(self):
        CoverageReport.objects.create(
            project=self.env.project,
            value=55.0,
            coverage_type=CoverageReport.TYPE_INCREMENTAL
        )
        self.mm_items_evaluation_task.run()
        report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertEqual(report.status, EvaluationReport.STATUS_PASS)

    def test_evaluation_should_calc_average_of_coverages_in_checking_period(self):
        out_of_period_time = timezone.now() - timedelta(days=self.CHECKING_PERIOD_DAYS + 1)
        with DjangoCurrentTimeMock(out_of_period_time):
            CoverageReport.objects.create(
                project=self.env.project,
                value=10,
                coverage_type=CoverageReport.TYPE_INCREMENTAL
            )
        CoverageReport.objects.create(
            project=self.env.project,
            value=30,
            coverage_type=CoverageReport.TYPE_INCREMENTAL
        )
        CoverageReport.objects.create(
            project=self.env.project,
            value=80,
            coverage_type=CoverageReport.TYPE_INCREMENTAL
        )
        self.mm_items_evaluation_task.run()
        report = EvaluationReport.get_latest(self.env.project, self.mm_item)
        self.assertEqual(float(report.current_value), 55.0)
        self.assertEqual(report.status, EvaluationReport.STATUS_PASS)
