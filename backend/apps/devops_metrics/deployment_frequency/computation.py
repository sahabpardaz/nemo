from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from apps.devops_metrics.metric_computer import MetricComputer
from apps.devops_metrics.models import Deployment


class DeploymentFrequencyComputer(MetricComputer[Optional[float]]):
    MINIMUM_DEPLOYMENTS_REQUIRED = 2

    # Override
    def compute_for_consecutive_timestamps(
            self,
            first_timestamp: datetime,
            num_timestamps: int,
            step_length: timedelta,
    ) -> List[Tuple[datetime, Optional[float]]]:
        last_timestamp = first_timestamp + (num_timestamps-1) * step_length
        all_deployment_times = Deployment.objects \
            .filter(environment=self.environment) \
            .filter(status=Deployment.STATUS_PASS) \
            .filter(time__gte=first_timestamp - self.checking_period) \
            .filter(time__lt=last_timestamp) \
            .order_by('time') \
            .values_list('time', flat=True)
        self._warn_about_performance_if_operations_count_is_too_large(num_timestamps * len(all_deployment_times))
        frequencies: List[Tuple[datetime, Optional[float]]] = []
        for i in range(num_timestamps):
            current_dt = first_timestamp + i * step_length
            checking_start_timestamp = current_dt - self.checking_period
            current_deployment_times = [t for t in all_deployment_times if checking_start_timestamp <= t < current_dt]
            total_count = len(current_deployment_times)
            if total_count < DeploymentFrequencyComputer.MINIMUM_DEPLOYMENTS_REQUIRED:
                freq = None
            else:
                freq = (max(current_deployment_times) - min(current_deployment_times)).total_seconds() / (total_count - 1)
            frequencies.append((current_dt, freq))
        return frequencies
