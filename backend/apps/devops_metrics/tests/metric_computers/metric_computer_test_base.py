from datetime import datetime, timedelta
from typing import Optional, Type

from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.utils import timezone

from apps.dashboard.models import MaturityModel, Project, Environment
from apps.devops_metrics.metric_computer import MetricComputer
from apps.devops_metrics.models import ChangeList, Deployment, ServiceStatusReport


class MetricComputerTestBase(TestCase):
    def setUp(self) -> None:
        self.maturity_model = MaturityModel.objects.create(name="test")
        self.user = User.objects.create(username="test")
        self.project = Project.objects.create(name="test", maturity_model=self.maturity_model, creator=self.user)
        self.environment = Environment.objects.create(name="test-env", project=self.project)
        self.now = timezone.make_aware(datetime(2000, 1, 1))

    def add_changelist(self, id: int, time: int, project: Optional[Project] = None) -> ChangeList:
        if project is None:
            project = self.project
        return ChangeList.objects.create(project=project,
                                         time=self.now + timedelta(seconds=time),
                                         change_list_id=str(id),
                                         commit_hash=str(id))

    def add_deployment(self, time: int, passed: bool, changelist: ChangeList) -> Deployment:
        return Deployment.objects.create(environment=self.environment,
                                         time=self.now + timedelta(seconds=time),
                                         status=Deployment.STATUS_PASS if passed else Deployment.STATUS_FAIL,
                                         change_list=changelist)

    def add_service_status_report(self, time: int, up: bool) -> ServiceStatusReport:
        return ServiceStatusReport.objects.create(environment=self.environment,
                                                  time=self.now + timedelta(seconds=time),
                                                  status=ServiceStatusReport.STATUS_UP if up else ServiceStatusReport.STATUS_DOWN)

    def _test_compute_for_single_timestamp(self, computer_cls: Type[MetricComputer], time: int, checking_period: int,
                                           expected_value: Optional[float]) -> None:
        computer = computer_cls(self.environment, timedelta(seconds=checking_period))
        value = computer.compute_for_single_timestamp(self.now + timedelta(seconds=time))
        self.assertEqual(value,
                         expected_value,
                         f"{computer_cls} calculated the metric wrongly! value={value}, time={time}, checking_period={checking_period}")
