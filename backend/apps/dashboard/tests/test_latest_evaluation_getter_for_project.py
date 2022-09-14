from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment
from apps.dashboard.models import EvaluationType, EvaluationReport, MaturityModelItem, Project, Environment
from apps.dashboard.project_retrieve_utils import LatestEvaluationReportFinder


class LatestEvaluationReportFinderTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
            validity_period_days=10,
            checking_period_days=10,
        )
        self.mm_item1 = MaturityModelItem.objects.create(
            code='0001',
            name='Manual1',
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        self.mm_item2 = MaturityModelItem.objects.create(
            code='0002',
            name='Manual2',
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        self.now = timezone.make_aware(datetime(2000, 1, 1))
        self.tommorow = self.now + timedelta(days=1)
        with DjangoCurrentTimeMock(self.now):
            EvaluationReport.objects.create(
                project=self.env.project,
                maturity_model_item=self.mm_item1,
                status=EvaluationReport.STATUS_PASS,
            )
            EvaluationReport.objects.create(
                project=self.env.project,
                maturity_model_item=self.mm_item2,
                status=EvaluationReport.STATUS_PASS,
            )

    def test_only_prefetched_items_should_be_accessible(self):
        latest_evaluation_report_finder = LatestEvaluationReportFinder(
            project=self.env.project,
            current_time=self.tommorow,
        )
        latest_evaluation_report_finder.prefetch_latest_evaluation_reports_for_mm_items([self.mm_item1.id])

        self.assertIsNotNone(latest_evaluation_report_finder.get_latest_evaluation_report_of_item(self.mm_item1.id))
        with self.assertRaises(ValueError):
            latest_evaluation_report_finder.get_latest_evaluation_report_of_item(self.mm_item2.id)

    def test_items_should_be_accessible_without_prefetch(self):
        latest_evaluation_report_finder = LatestEvaluationReportFinder(
            project=self.env.project,
            current_time=self.tommorow,
        )
        item_ids = (self.mm_item1.id, self.mm_item2.id)
        for item_id in item_ids:
            self.assertIsNotNone(
                latest_evaluation_report_finder.get_latest_evaluation_report_of_item(item_id)
            )

    def test_all_items_in_prefetch_should_be_accessible(self):
        latest_evaluation_report_finder = LatestEvaluationReportFinder(
            project=self.env.project,
            current_time=self.tommorow,
        )
        item_ids = (self.mm_item1.id, self.mm_item2.id)
        latest_evaluation_report_finder.prefetch_latest_evaluation_reports_for_mm_items(item_ids)
        for item_id in item_ids:
            self.assertIsNotNone(
                latest_evaluation_report_finder.get_latest_evaluation_report_of_item(item_id)
            )

    def test_extra_fields_should_be_returned_without_any_additional_db_query(self):
        extra_field = 'current_value'
        latest_evaluation_report_finder = LatestEvaluationReportFinder(
            project=self.env.project,
            current_time=self.tommorow,
            evaluation_reports_extra_fields=[extra_field],
        )
        latest_evaluation_report_finder.prefetch_latest_evaluation_reports_for_mm_items([self.mm_item1.id])
        with self.assertNumQueries(0):
            getattr(latest_evaluation_report_finder.get_latest_evaluation_report_of_item(self.mm_item1.id), extra_field)

    def test_just_one_database_query_required_for_prefetched_items_evaluation_report(self):
        expected_queries_count = 1
        with self.assertNumQueries(expected_queries_count):
            latest_evaluation_report_finder = LatestEvaluationReportFinder(
                project=self.env.project,
                current_time=self.tommorow,
            )
            item_ids = (self.mm_item1.id, self.mm_item2.id)
            latest_evaluation_report_finder.prefetch_latest_evaluation_reports_for_mm_items(item_ids)
            for item_id in item_ids:
                latest_evaluation_report_finder.get_latest_evaluation_report_of_item(item_id)

    def test_evaluation_report_with_newer_latest_evaluation_time_should_be_returned(self):
        newer_evaluation_report_time = self.now + timedelta(hours=1)
        with DjangoCurrentTimeMock(newer_evaluation_report_time):
            EvaluationReport.objects.create(
                project=self.env.project,
                maturity_model_item=self.mm_item1,
                status=EvaluationReport.STATUS_PASS,
                description="Newer Report",
            )

        latest_evaluation_report_finder = LatestEvaluationReportFinder(
            project=self.env.project,
            current_time=self.tommorow,
        )
        self.assertEquals(
            latest_evaluation_report_finder.get_latest_evaluation_report_of_item(self.mm_item1.id).latest_evaluation_time,
            newer_evaluation_report_time
        )

    def test_only_evaluation_reports_less_than_current_time_should_be_returned(self):
        tommorows_evaluation_report_time = self.tommorow + timedelta(hours=1)
        with DjangoCurrentTimeMock(tommorows_evaluation_report_time):
            EvaluationReport.objects.create(
                project=self.env.project,
                maturity_model_item=self.mm_item1,
                status=EvaluationReport.STATUS_PASS,
            )

        latest_evaluation_report_finder = LatestEvaluationReportFinder(
            project=self.env.project,
            current_time=self.tommorow,
        )
        self.assertNotEquals(
            latest_evaluation_report_finder.get_latest_evaluation_report_of_item(self.mm_item1.id).latest_evaluation_time,
            tommorows_evaluation_report_time
        )

    def test_only_evaluation_reports_of_given_project_should_be_returned(self):
        another_project = self._create_new_project()
        another_project_evaluation_report_status = EvaluationReport.STATUS_FAIL
        with DjangoCurrentTimeMock(self.now):
            EvaluationReport.objects.create(
                project=another_project,
                maturity_model_item=self.mm_item1,
                status=another_project_evaluation_report_status,
            )
        latest_evaluation_report_finder = LatestEvaluationReportFinder(
            project=another_project,
            current_time=self.tommorow,
        )
        self.assertEquals(
            latest_evaluation_report_finder.get_latest_evaluation_report_of_item(self.mm_item1.id).status,
            another_project_evaluation_report_status
        )

    def _create_new_project(self):
        project = Project.objects.create(name='Another Project',
                                     maturity_model=self.env.maturity_model,
                                     creator_id=self.env.user.id)
        environment = Environment.objects.create(project=project, name="Default Environment")
        project.default_environment = environment
        project.save()
        return project
