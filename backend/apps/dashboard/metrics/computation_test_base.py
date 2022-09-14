import math
from abc import ABC, abstractmethod
from typing import List, Generic
from datetime import timedelta, datetime

from apps.utils.general_utils import coalesce
from apps.dashboard.metrics.computation_base import TMetric, ConsecutiveTimestampsMetricComputerMixin


def _are_approximately_the_same(a, b):
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-5)
    if (isinstance(a, list) and isinstance(b, list)) or (isinstance(a, tuple) and isinstance(b, tuple)):
        if len(a) != len(b):
            return False
        for a_i, b_i in zip(a, b):
            if not _are_approximately_the_same(a_i, b_i):
                return False
        return True
    # We should handle dicts too. But it is not needed in our case.
    if isinstance(a, dict) or isinstance(b, dict):
        raise NotImplementedError()
    return a == b


class ConsecutiveTimestampsMetricComputerTestingMixin(ABC, Generic[TMetric]):

    @abstractmethod
    def get_computer(self, *args, **kwargs) -> ConsecutiveTimestampsMetricComputerMixin[TMetric]:
        pass


    def check_metric_computation(
            self,
            expected: TMetric,
            timestamp: datetime,
            *computer_init_args,
            **computer_init_kwargs,
    ):
        c = self.get_computer(*computer_init_args, **computer_init_kwargs,)
        computed = c.compute_for_single_timestamp(timestamp)
        if not _are_approximately_the_same(computed, expected):
            self.fail(f"""\
Wrong computation of metric.
timestamp={timestamp}
computer_init_args={computer_init_args}
computer_init_kwargs={computer_init_kwargs}
expected={expected}
computed={computed}
""")

    def check_metric_consecutive_computation(
            self,
            expected_values: List[TMetric],
            first_timestamp: datetime,
            *computer_init_args,
            step_length: timedelta = None,
            **computer_init_kwargs,
    ):
        step_length = coalesce(step_length, ConsecutiveTimestampsMetricComputerMixin.DEFAULT_CONSECUTIVE_TIMESTAMPS_DIFFERENCE)
        num_timestamps = len(expected_values)
        expected = [(first_timestamp+timedelta(days=i), v) for i, v in enumerate(expected_values)]
        c = self.get_computer(*computer_init_args, **computer_init_kwargs,)
        computed = c.compute_for_consecutive_timestamps(
            first_timestamp=first_timestamp,
            num_timestamps=num_timestamps,
            step_length=step_length,
        )
        if not _are_approximately_the_same(computed, expected):
            self.fail(f"""\
Wrong computation of metrics for consecutive days.
first_timestamp={first_timestamp}
num_timestamps={num_timestamps}
step_length={step_length}
computer_init_args={computer_init_args}
computer_init_kwargs={computer_init_kwargs}
expected={expected}
computed={computed}
""")

    def check_all_combinations_of_consecutive_timestamps(
            self,
            expected_values: List[TMetric],
            first_timestamp: datetime,
            *computer_init_args,
            step_length: timedelta = None,
            **computer_init_kwargs,
    ):
        """
        Gets expected values for some consecutive timestamps,
         and verifies the correctness of computation for each single timestamp i
         and also for each interval [i, ..., j] of timestamps.
        All the results should match the expected values.
        """
        step_length = coalesce(step_length, ConsecutiveTimestampsMetricComputerMixin.DEFAULT_CONSECUTIVE_TIMESTAMPS_DIFFERENCE)
        num_timestamps = len(expected_values)
        timestamps = [first_timestamp + i * step_length for i in range(num_timestamps)]
        for i in range(num_timestamps):
            self.check_metric_computation(
                expected=expected_values[i],
                timestamp=timestamps[i],
                *computer_init_args,
                **computer_init_kwargs,
            )
        for j in range(num_timestamps):
            for i in range(j+1):
                self.check_metric_consecutive_computation(
                    expected_values=expected_values[i:j+1],
                    first_timestamp=timestamps[i],
                    step_length=step_length,
                    *computer_init_args,
                    **computer_init_kwargs,
                )
