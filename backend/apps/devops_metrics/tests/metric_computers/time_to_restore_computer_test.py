from apps.devops_metrics.tests.metric_computers.metric_computer_test_base import MetricComputerTestBase
from apps.devops_metrics.time_to_restore.computation import TimeToRestoreComputer


class TimeToRestoreComputerTest(MetricComputerTestBase):
    def test_ttr_should_be_time_diff_from_down_report_to_up_report(self):
        self.add_service_status_report(time=100, up=False)
        self.add_service_status_report(time=150, up=True)
        self._test_compute_for_single_timestamp(TimeToRestoreComputer, time=200, checking_period=200, expected_value=50)

    def test_situation_down_in_end_of_period_should_not_affect_time_to_restore(self):
        self.add_service_status_report(time=200, up=False)
        self.add_service_status_report(time=220, up=True)
        self.add_service_status_report(time=450, up=False)
        self._test_compute_for_single_timestamp(TimeToRestoreComputer, time=500, checking_period=400, expected_value=20)

    def test_situation_multiple_downs_should_not_affect_time_to_restore(self):
        self.add_service_status_report(time=230, up=False)
        self.add_service_status_report(time=250, up=False)
        self.add_service_status_report(time=270, up=False)
        self.add_service_status_report(time=360, up=True)
        self._test_compute_for_single_timestamp(TimeToRestoreComputer, time=500, checking_period=400,
                                                expected_value=130)

    def test_situation_multiple_ups_should_not_affect_time_to_restore(self):
        self.add_service_status_report(time=150, up=False)
        self.add_service_status_report(time=170, up=True)
        self.add_service_status_report(time=220, up=True)
        self._test_compute_for_single_timestamp(TimeToRestoreComputer, time=500, checking_period=500, expected_value=20)

    def test_time_to_restore_should_be_0_when_no_report_exists(self):
        self._test_compute_for_single_timestamp(TimeToRestoreComputer, time=10, checking_period=10, expected_value=0)
