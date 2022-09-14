from apps.devops_metrics.change_failure_rate.computation import ChangeFailureRateComputer
from apps.devops_metrics.tests.metric_computers.metric_computer_test_base import MetricComputerTestBase


class ChangeFailureRateComputerTest(MetricComputerTestBase):
    def test_cfr_should_be_50_with_2_deploys(self):
        cl = self.add_changelist(id=0, time=100)
        self.add_deployment(time=150, passed=True, changelist=cl)
        self.add_deployment(time=160, passed=False, changelist=cl)
        self._test_compute_for_single_timestamp(ChangeFailureRateComputer, time=200, checking_period=200,
                                                expected_value=50)

    def test_cfr_should_be_0_when_all_deployments_are_passed(self):
        cl = self.add_changelist(id=0, time=100)
        self.add_deployment(time=150, passed=True, changelist=cl)
        self._test_compute_for_single_timestamp(ChangeFailureRateComputer, time=200, checking_period=200,
                                                expected_value=0)

    def test_cfr_should_be_100_when_all_deployments_are_failed(self):
        cl = self.add_changelist(id=0, time=100)
        self.add_deployment(time=150, passed=False, changelist=cl)
        self._test_compute_for_single_timestamp(ChangeFailureRateComputer, time=200, checking_period=200,
                                                expected_value=100)

    def test_deployments_out_of_checking_period_should_be_ignored(self):
        cl = self.add_changelist(id=0, time=100)
        self.add_deployment(time=150, passed=True, changelist=cl)
        self.add_deployment(time=250, passed=False, changelist=cl)
        self._test_compute_for_single_timestamp(ChangeFailureRateComputer, time=200, checking_period=200,
                                                expected_value=0)

    def test_deployment_inside_checking_period_should_not_be_ignored_even_if_its_cl_is_out_of_checking_period(self):
        cl = self.add_changelist(id=0, time=10)
        self.add_deployment(time=150, passed=True, changelist=cl)
        self.add_deployment(time=160, passed=False, changelist=cl)
        self._test_compute_for_single_timestamp(ChangeFailureRateComputer, time=200, checking_period=180,
                                                expected_value=50)

    def test_cfr_should_be_none_when_no_data_exist(self):
        self._test_compute_for_single_timestamp(ChangeFailureRateComputer, time=200, checking_period=200,
                                                expected_value=None)
