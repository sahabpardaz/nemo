import logging
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Tuple, TypeVar, Generic
from django.conf import settings

import pytz
from apps.devops_metrics.serializers import MetricDataPointSerializer

from apps.utils import general_utils


logger = logging.getLogger(__name__)

TMetric = TypeVar('TMetric')


class ConsecutiveTimestampsMetricComputerMixin(ABC, Generic[TMetric]):
    DEFAULT_CONSECUTIVE_TIMESTAMPS_DIFFERENCE = timedelta(days=1)

    _DEFAULT_COMPUTE_OPERATIONS_THRESHOLD = 100_000_000

    def compute_for_single_timestamp(self, timestamp: datetime) -> TMetric:
        data_list = self.compute_for_consecutive_timestamps(
            first_timestamp=timestamp,
            num_timestamps=1,
            step_length=ConsecutiveTimestampsMetricComputerMixin.DEFAULT_CONSECUTIVE_TIMESTAMPS_DIFFERENCE,
        )
        assert len(data_list) == 1, f"Expected data_list to have one item but got: {len(data_list)}"
        data_item = data_list[0]
        assert len(data_item) == 2, f"Expected data_item to be a tuple of length 2 but got: {len(data_item)}"
        return data_item[1]

    @abstractmethod
    def compute_for_consecutive_timestamps(
            self,
            first_timestamp: datetime,
            num_timestamps: int,
            step_length: timedelta,
    ) -> List[Tuple[datetime, TMetric]]:
        # len(result) == num_timestamps
        pass

    def get_daily_graph_data_serialized(self, period_start_date: date, period_end_date: date) -> List[Dict]:
        local_timezone = pytz.timezone(settings.TIME_ZONE)
        period_days = (period_end_date - period_start_date).days + 1
        first_dt_next_day_at_00 = general_utils.convert_date_to_datetime(period_start_date + timedelta(days=1),
                                                                         time.min.replace(tzinfo=local_timezone))
        daily_metrics = self.compute_for_consecutive_timestamps(
            first_timestamp=first_dt_next_day_at_00,
            num_timestamps=period_days,
            step_length=ConsecutiveTimestampsMetricComputerMixin.DEFAULT_CONSECUTIVE_TIMESTAMPS_DIFFERENCE,
        )
        daily_metrics_one_day_offset = []
        for date, value in daily_metrics:
            daily_metrics_one_day_offset += [(date - timedelta(days=1), value)]
        return MetricDataPointSerializer(daily_metrics_one_day_offset, many=True).data

    def _warn_about_performance_if_operations_count_is_too_large(self, operations_count: int, compute_operations_thresholds: int = None) -> None:
        if compute_operations_thresholds is None:
            compute_operations_thresholds = ConsecutiveTimestampsMetricComputerMixin._DEFAULT_COMPUTE_OPERATIONS_THRESHOLD
        if operations_count > compute_operations_thresholds:
            # TODO: switch to warning log when issue #11714 is done.
            logger.error(f"""\
During a computation in '{self.__class__.__name__}', encountered a higher operations count than expected ({compute_operations_thresholds}).
data_len * MAX_PERIOD_IN_DAYS > compute_operations_thresholds
==> {operations_count} > {compute_operations_thresholds}
Consider optimizing the computation algorithm, for the sake of probable performance issues.""")
