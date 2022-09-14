from django.test import TestCase
from rest_framework import serializers
from apps.dashboard.models import CoverageReport
from apps.dashboard.serializers import CoverageReportSerializer
from apps.dashboard.tests.utils import setup_basic_environment


class CoverageReportSerializerTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()

    def test_multiple_coverage_reports_should_be_created_with_empty_version(self):
        self._create_coverage_report()
        self._create_coverage_report()

    def test_multiple_coverage_report_should_not_be_created_with_duplicate_version(self):
        version = '1.1.0,2.0.1'
        self._create_coverage_report(version)
        with self.assertRaises(serializers.ValidationError):
            self._create_coverage_report(version)

    def _create_coverage_report(self, version='', coverage_type=CoverageReport.TYPE_OVERALL, value=50):
        return CoverageReportSerializer.validate_and_save(
            data={
                'version': version,
                'coverage_type': coverage_type,
                'value': value,
            },
            context={
                'project_id': self.env.project.id,
            }
        )
