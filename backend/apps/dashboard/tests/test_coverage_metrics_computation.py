from datetime import timedelta
from statistics import mean
from django.utils import timezone
from django.test import TestCase
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment
from apps.dashboard.models import CoverageReport


class OverallCoverageComputationTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()

    def test_should_return_none_when_no_report_exists(self):
        overall_coverage_value = CoverageReport.compute_overall_coverage(self.env.project)
        self.assertEqual(overall_coverage_value, None)

    def test_should_return_latest_report_value(self):
        values = [10, 30, 80]
        for value in values:
            CoverageReport.objects.create(
                project=self.env.project,
                value=value,
                coverage_type=CoverageReport.TYPE_OVERALL,
            )
        overall_coverage_value = CoverageReport.compute_overall_coverage(self.env.project)
        self.assertEqual(overall_coverage_value, values[-1])

    def test_should_return_none_when_no_report_exists_after_specific_date(self):
        coverage_time = timezone.now() - timedelta(days=1)
        with DjangoCurrentTimeMock(coverage_time):
            CoverageReport.objects.create(
                project=self.env.project,
                value=50,
                coverage_type=CoverageReport.TYPE_OVERALL,
            )
        overall_coverage_value = CoverageReport.compute_overall_coverage(
            self.env.project,
            (coverage_time + timedelta(days=1)).date(),
        )
        self.assertEqual(overall_coverage_value, None)


class IncrementalCoverageComputationTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()

    def test_should_return_none_when_no_report_exists(self):
        incremental_coverage_value = CoverageReport.compute_incremental_coverage(self.env.project)
        self.assertEqual(incremental_coverage_value, None)

    def test_should_return_average_of_reports_value(self):
        values = [10, 30, 80]
        for value in values:
            CoverageReport.objects.create(
                project=self.env.project,
                value=value,
                coverage_type=CoverageReport.TYPE_INCREMENTAL,
            )
        incremental_coverage_value = CoverageReport.compute_incremental_coverage(self.env.project)
        self.assertEqual(incremental_coverage_value, mean(values))

    def test_should_return_none_when_no_report_exists_after_specific_date(self):
        coverage_time = timezone.now() - timedelta(days=1)
        CoverageReport.objects.create(
            project=self.env.project,
            value=50,
            coverage_type=CoverageReport.TYPE_INCREMENTAL,
            creation_time=coverage_time,
        )
        incremental_coverage_value = CoverageReport.compute_overall_coverage(self.env.project, coverage_time + timedelta(days=1))
        self.assertEqual(incremental_coverage_value, None)
