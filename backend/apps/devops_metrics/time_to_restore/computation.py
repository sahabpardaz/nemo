from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Any, Dict

from apps.devops_metrics.metric_computer import MetricComputer
from apps.devops_metrics.models import ServiceStatusReport


class TimeToRestoreComputer(MetricComputer[Optional[int]]):

    # Override
    def compute_for_consecutive_timestamps(
            self,
            first_timestamp: datetime,
            num_timestamps: int,
            step_length: timedelta,
    ) -> List[Tuple[datetime, Optional[int]]]:
        last_timestamp = first_timestamp + (num_timestamps-1) * step_length
        all_sit_change_times = list(ServiceStatusReport.objects
                                    .filter(environment=self.environment)
                                    .filter(time__gte=first_timestamp - self.checking_period)
                                    .filter(time__lt=last_timestamp)
                                    .order_by('time')
                                    .only('time', 'status')
                                    .seal())
        ttrs: List[Tuple[datetime, Optional[int]]] = []
        self._warn_about_performance_if_operations_count_is_too_large(num_timestamps * len(all_sit_change_times))
        for i in range(num_timestamps):
            current_dt = first_timestamp + i * step_length
            avg_ttr = self._compute_single_timestamp_avg_ttr(all_sit_change_times, current_dt)
            ttrs.append((current_dt, int(avg_ttr.total_seconds()) if avg_ttr is not None else 0))
        return ttrs

    def _compute_single_timestamp_avg_ttr(self, all_sit_change_times: List[Dict[str, Any]], current_dt: datetime) -> Optional[timedelta]:
        checking_first_dt = current_dt - self.checking_period
        total_down_time = timedelta(0)
        last_down_report: Optional[Dict[str, Any]] = None
        count = 0
        for sit_change in all_sit_change_times:
            if not checking_first_dt <= sit_change.time < current_dt:
                continue
            if sit_change.status == ServiceStatusReport.STATUS_DOWN:
                if last_down_report is None:
                    last_down_report = sit_change
            else:
                if last_down_report is None:
                    continue
                else:
                    total_down_time += sit_change.time - last_down_report.time
                    count += 1
                    last_down_report = None
        return total_down_time / count if count > 0 else None
