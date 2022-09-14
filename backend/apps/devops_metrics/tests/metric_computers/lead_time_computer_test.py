import sys
from datetime import datetime, timedelta

from django.utils import timezone

from apps.dashboard.models import Project
from apps.devops_metrics.lead_time.computation import LeadTimeComputer
from apps.devops_metrics.models import ChangeList
from apps.devops_metrics.tests.metric_computers.metric_computer_test_base import MetricComputerTestBase


class LeadTimeComputerTest(MetricComputerTestBase):
    def test_lead_time_should_be_time_diff_of_changelist_to_its_deployment(self):
        cl = self.add_changelist(id=0, time=100)
        self.add_deployment(time=150, passed=True, changelist=cl)
        self._test_compute_for_single_timestamp(LeadTimeComputer, time=200, checking_period=200, expected_value=50)

    def test_changelists_out_of_checking_period_should_not_affect_lead_time(self):
        cl0 = self.add_changelist(0, 10)
        cl1 = self.add_changelist(1, 110)
        self.add_deployment(time=150, changelist=cl0, passed=True)
        self.add_deployment(time=160, changelist=cl1, passed=True)
        self._test_compute_for_single_timestamp(LeadTimeComputer, time=200, checking_period=150, expected_value=50)

    def test_deployments_out_of_checking_period_should_not_affect_lead_time(self):
        cl0 = self.add_changelist(0, 10)
        cl1 = self.add_changelist(1, 110)
        self.add_deployment(time=150, changelist=cl0, passed=True)
        self.add_deployment(time=160, changelist=cl1, passed=True)
        self._test_compute_for_single_timestamp(LeadTimeComputer, time=155, checking_period=155, expected_value=140)

    def test_later_explicit_deployment_should_not_affect_leadtime_when_earlier_implicit_deployment_exists(self):
        changelists = [
            self.add_changelist(0, 100),
            self.add_changelist(1, 200),
        ]
        self.add_deployment(time=300, passed=True, changelist=changelists[1])
        self.add_deployment(time=400, passed=True, changelist=changelists[0])

        self._test_compute_for_single_timestamp(LeadTimeComputer, time=500, checking_period=400, expected_value=150)

    def test_failed_deployments_should_not_affect_lead_time(self):
        cl = self.add_changelist(id=0, time=10)
        self.add_deployment(time=100, passed=False, changelist=cl)
        self.add_deployment(time=150, passed=True, changelist=cl)
        self._test_compute_for_single_timestamp(LeadTimeComputer, time=200, checking_period=200, expected_value=140)

    def test_changelists_of_other_projects_should_not_affect_leadtime(self):
        another_project = Project.objects.create(name="test2", maturity_model=self.maturity_model, creator=self.user)
        out_changelist = self.add_changelist(0, 100, another_project)

        in_changelist = self.add_changelist(1, 200)
        self.add_deployment(time=300, passed=True, changelist=in_changelist)

        self._test_compute_for_single_timestamp(LeadTimeComputer, time=600, checking_period=600, expected_value=100)

    def test_large_number_of_changelists_shouldnt_make_recursion_problem(self):
        change_lists_count = sys.getrecursionlimit() + 1
        time = timezone.make_aware(datetime(2000, 1, 1, 2, 0))
        change_lists = [ChangeList(project=self.project,
                                   commit_hash=str(i),
                                   change_list_id=str(i),
                                   time=time) for i in range(change_lists_count)]
        ChangeList.objects.bulk_create(change_lists)
        computer = LeadTimeComputer(self.environment, checking_period=timedelta(seconds=2))
        lead_time = computer.compute_for_single_timestamp(time + timedelta(seconds=1))
        self.assertIsNone(lead_time)
