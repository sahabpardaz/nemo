import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from abc import abstractmethod
from statistics import mean

from django.db import models

from apps.dashboard.models import Project, CoverageReport
from apps.dashboard.metrics.computation_base import ConsecutiveTimestampsMetricComputerMixin

logger = logging.getLogger(__name__)


class CoverageMetricComputerBase(ConsecutiveTimestampsMetricComputerMixin[float]):

    def __init__(self, project: Project, checking_period: Optional[timedelta] = None):
        self.project = project
        self.checking_period = checking_period

    @abstractmethod
    def coverage_type(self):
        pass

    @abstractmethod
    def compute_for_reports(self, coverage_reports) -> Optional[float]:
        pass

    def _get_queryset_for_interval(self, first_timestamp: datetime, last_timestamp: datetime):
        qs = (
            CoverageReport.objects
            .filter(coverage_type=self.coverage_type())
            .filter(project=self.project)
            .only('value', 'last_update_time')
            .seal()
            .filter(last_update_time__lt=last_timestamp)
            .order_by('last_update_time')
        )
        # TODO (issue #12951): Check if it is really valid to have None for checking_period.
        if self.checking_period is not None:
            qs = qs.filter(last_update_time__gte=first_timestamp - self.checking_period)
        return qs

    # Override
    def compute_for_consecutive_timestamps(
            self,
            first_timestamp: datetime,
            num_timestamps: int,
            step_length: timedelta,
    ) -> List[Tuple[datetime, Optional[float]]]:
        last_timestamp = first_timestamp + (num_timestamps-1) * step_length
        qs = self._get_queryset_for_interval(first_timestamp, last_timestamp)
        coverage_reports = list(qs)
        self._warn_about_performance_if_operations_count_is_too_large(num_timestamps * len(coverage_reports))
        data_points: List[Tuple[datetime, Optional[float]]] = []
        for i in range(num_timestamps):
            current_timestamp = first_timestamp + timedelta(days=i)
            if self.checking_period is None:
                current_coverage_reports = [r for r in coverage_reports if r.last_update_time < current_timestamp]
            else:
                checking_start_timestamp = current_timestamp - self.checking_period
                current_coverage_reports = [r for r in coverage_reports if checking_start_timestamp <= r.last_update_time < current_timestamp]
            data_points.append((current_timestamp, self.compute_for_reports(current_coverage_reports)))
        return data_points


class OverallCoverageComputer(CoverageMetricComputerBase):

    # Override
    def coverage_type(self):
        return CoverageReport.TYPE_OVERALL

    # Override
    def compute_for_reports(self, coverage_reports) -> Optional[float]:
        return coverage_reports[-1].value if coverage_reports else None

    # Override
    # This is overrided with an implementation with much higher performance
    #  since it is called frequently for the first page.
    def compute_for_single_timestamp(self, timestamp: datetime) -> Optional[float]:
        qs = self._get_queryset_for_interval(timestamp, timestamp)
        last_coverage_report = qs.last()
        return last_coverage_report.value if last_coverage_report else None


class IncrementalCoverageComputer(CoverageMetricComputerBase):

    # Override
    def coverage_type(self):
        return CoverageReport.TYPE_INCREMENTAL

    # Override
    def compute_for_reports(self, coverage_reports) -> Optional[float]:
        return mean(r.value for r in coverage_reports) if coverage_reports else None

    # Override
    # This is overrided with an implementation with much higher performance
    #  since it is called frequently for the first page.
    def compute_for_single_timestamp(self, timestamp: datetime) -> Optional[float]:
        qs = self._get_queryset_for_interval(timestamp, timestamp)
        aggr = qs.aggregate(val_avg=models.Avg('value'))
        return aggr['val_avg']
