from apps.devops_metrics.deployment_frequency.computation import DeploymentFrequencyComputer
from apps.devops_metrics.tests.metric_computers.metric_computer_test_base import MetricComputerTestBase


class DeploymentFrequencyComputerTest(MetricComputerTestBase):
    def test_deployment_frequency_should_be_time_diff_of_2_deploys(self):
        cl = self.add_changelist(id=0, time=100)
        self.add_deployment(time=150, passed=True, changelist=cl)
        self.add_deployment(time=160, passed=True, changelist=cl)
        self._test_compute_for_single_timestamp(DeploymentFrequencyComputer, time=200, checking_period=200,
                                                expected_value=10)

    def test_deployments_out_of_checking_period_should_not_affect_deployment_frequency(self):
        cl = self.add_changelist(id=0, time=100)
        self.add_deployment(time=150, passed=True, changelist=cl)
        self.add_deployment(time=160, passed=True, changelist=cl)
        self.add_deployment(time=250, passed=True, changelist=cl)
        self._test_compute_for_single_timestamp(DeploymentFrequencyComputer, time=200, checking_period=200,
                                                expected_value=10)

    def test_redeployment_should_affect_deployment_frequency(self):
        changelist = self.add_changelist(0, 100)

        self.add_deployment(time=200, passed=True, changelist=changelist)
        self.add_deployment(time=300, passed=True, changelist=changelist)

        self._test_compute_for_single_timestamp(DeploymentFrequencyComputer, time=500, checking_period=400,
                                                expected_value=100)

    def test_failed_deployments_should_not_affect_deployment_frequency(self):
        changelist = self.add_changelist(0, 100)
        self.add_deployment(time=200, passed=True, changelist=changelist)
        self.add_deployment(time=300, passed=False, changelist=changelist)
        self.add_deployment(time=400, passed=True, changelist=changelist)

        self._test_compute_for_single_timestamp(DeploymentFrequencyComputer, time=500, checking_period=400,
                                                expected_value=200)
