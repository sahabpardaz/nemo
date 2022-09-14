from datetime import timedelta, datetime
from django.utils import timezone
from django.test import TestCase
from apps.dashboard.evaluators.devops_metrics_evaluators import LeadTimeEvaluator
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment
from apps.dashboard.models import EvaluationType, EvaluationReport, MaturityModelItem, Environment
from apps.devops_metrics.models import ChangeList, Deployment


class EvaluatorTest(TestCase):
    """
    LeadTimeEvaluator used as an arbitary evaluator.
    """
    def setUp(self):
        self.env = setup_basic_environment()
        environment = Environment.objects.create(
            project=self.env.project,
            name="default",
            description=None,
        )
        self.env.project.default_environment = environment
        self.env.project.save()
        self.now = timezone.make_aware(datetime(2000, 1, 1))
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_LEAD_TIME,
            checking_period_days=1,
            validity_period_days=1,
        )
        self.mm_item = MaturityModelItem.objects.create(
            code="T000",
            name="Test",
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value=2,
            acceptable_value_type=MaturityModelItem.VALUE_TYPE_SECONDS,
        )

    def test_happy_path(self):
        change_list = self.add_changelist(1, 0)
        self.add_deployment(4, True, change_list)

        with DjangoCurrentTimeMock(self.now + timedelta(days=1)):
            arbitrary_devops_metric_evaluator = LeadTimeEvaluator()
            generated_evaluation_report = arbitrary_devops_metric_evaluator.evaluate(self.env.project, self.mm_item)

        self.assertEqual(generated_evaluation_report.status, EvaluationReport.STATUS_FAIL)
        self.assertEqual(generated_evaluation_report.current_value, 4)

    def add_changelist(self, id: int, time: int) -> ChangeList:
        return ChangeList.objects.create(project=self.env.project,
                                         time=self.now + timedelta(seconds=time),
                                         change_list_id=str(id),
                                         commit_hash=str(id))

    def add_deployment(self, time: int, passed: bool, changelist: ChangeList) -> Deployment:
        return Deployment.objects.create(environment=self.env.project.default_environment,
                                         time=self.now + timedelta(seconds=time),
                                         status=Deployment.STATUS_PASS if passed else Deployment.STATUS_FAIL,
                                         change_list=changelist)
