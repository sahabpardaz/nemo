from datetime import timedelta

from parameterized import parameterized

from apps.devops_metrics.change_failure_rate.computation import ChangeFailureRateComputer
from apps.devops_metrics.deployment_frequency.computation import DeploymentFrequencyComputer
from apps.devops_metrics.lead_time.computation import LeadTimeComputer
from apps.devops_metrics.tests.metric_computers.metric_computer_test_base import MetricComputerTestBase
from apps.devops_metrics.time_to_restore.computation import TimeToRestoreComputer


class MetricComputersGeneralTest(MetricComputerTestBase):
    @parameterized.expand([
        (ChangeFailureRateComputer,),
        (DeploymentFrequencyComputer,),
        (TimeToRestoreComputer,),
        (LeadTimeComputer,),
    ])
    def test_single_computation_should_be_consistent_with_consecutive_computation(self, computer_cls):
        cl = self.add_changelist(id=0, time=100)
        self.add_deployment(time=150, passed=True, changelist=cl)
        self.add_deployment(time=160, passed=False, changelist=cl)
        self.add_deployment(time=170, passed=True, changelist=cl)
        self.add_service_status_report(time=180, up=False)
        self.add_service_status_report(time=190, up=True)

        metric_computation_timestamp = self.now + timedelta(seconds=200)
        checking_period = timedelta(seconds=400)
        computer = computer_cls(self.environment, checking_period)
        value_from_single_computation = computer.compute_for_single_timestamp(metric_computation_timestamp)
        _, value_from_consecutive_computation = computer.compute_for_consecutive_timestamps(
            first_timestamp=metric_computation_timestamp - timedelta(seconds=100),
            num_timestamps=5,
            step_length=timedelta(seconds=100))[1]
        self.assertEqual(value_from_single_computation, value_from_consecutive_computation)
