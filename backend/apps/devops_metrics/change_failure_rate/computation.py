import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

from apps.devops_metrics.metric_computer import MetricComputer
from apps.devops_metrics.models import Deployment

logger = logging.getLogger(__name__)


class ChangeFailureRateComputer(MetricComputer[Optional[float]]):

    # Override
    def compute_for_consecutive_timestamps(
            self,
            first_timestamp: datetime,
            num_timestamps: int,
            step_length: timedelta,
    ) -> List[Tuple[datetime, Optional[float]]]:
        last_timestamp = first_timestamp + (num_timestamps-1) * step_length
        all_deployments = list(Deployment.objects
                               .filter(environment=self.environment)
                               .filter(time__gte=first_timestamp - self.checking_period)
                               .filter(time__lt=last_timestamp)
                               .order_by('time')
                               .only('time', 'status')
                               .seal())
        self._warn_about_performance_if_operations_count_is_too_large(num_timestamps * len(all_deployments))
        rates: List[Tuple[datetime, Optional[float]]] = []
        for i in range(num_timestamps):
            current_dt = first_timestamp + i * step_length
            checking_start_timestamp = current_dt - self.checking_period
            current_deployments = [d for d in all_deployments if checking_start_timestamp <= d.time < current_dt]
            failed_deployments = [d for d in current_deployments if d.status == Deployment.STATUS_FAIL]
            total_count = len(current_deployments)
            failed_count = len(failed_deployments)
            rate = (failed_count / total_count) * 100 if total_count > 0 else None
            rates.append((current_dt, rate))
        return rates
