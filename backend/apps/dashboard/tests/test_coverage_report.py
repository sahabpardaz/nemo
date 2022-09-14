from rest_framework import status
from rest_framework.test import APITestCase
from apps.dashboard.tasks import AutomaticMMItemsEvaluation
from apps.dashboard.models import EvaluationReport, MaturityModelItem
from apps.dashboard.models import CoverageReport, EvaluationType
from apps.dashboard.tests.utils import setup_basic_environment


class CoverageEvaluationTest(APITestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()
        test_coverage_evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_TEST_COVERAGE,
            checking_period_days=1,
            validity_period_days=2,
        )
        self.coverage_mm_item = MaturityModelItem(name='Coverage',
                                                  evaluation_type=test_coverage_evaluation_type,
                                                  acceptable_value=50,
                                                  acceptable_value_type=MaturityModelItem.VALUE_TYPE_PERCENTAGE,
                                                  maturity_model_level=self.env.maturity_model_level)
        self.coverage_mm_item.save()

    def test_evaluation_should_success_when_coverage_reported(self):
        sample_coverage_value = '83.54'
        CoverageReport.objects.create(value=sample_coverage_value,
                                      coverage_type=CoverageReport.TYPE_OVERALL,
                                      project=self.env.project)
        AutomaticMMItemsEvaluation().run()
        latest_report = EvaluationReport.get_latest(self.env.project, self.coverage_mm_item)
        self.assertEqual(latest_report.status, EvaluationReport.STATUS_PASS)
        self.assertEqual(latest_report.current_value, sample_coverage_value)

    def test_report_by_project_token(self):
        response = self.client.post(f'/v1/dashboard/project/{self.env.project.id}/coverage-report/',
                                    data={'value': '45.76', 'coverage_type': CoverageReport.TYPE_INCREMENTAL},
                                    format='json',
                                    **{'HTTP_NEMO_PROJECT_TOKEN': self.env.project.auth_token.key})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
