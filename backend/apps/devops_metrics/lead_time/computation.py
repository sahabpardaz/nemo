import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from apps.devops_metrics.metric_computer import MetricComputer
from apps.devops_metrics.models import ChangeList, Deployment

logger = logging.getLogger(__name__)


class LeadTimeComputer(MetricComputer[Optional[int]]):

    # Override
    def compute_for_consecutive_timestamps(
            self,
            first_timestamp: datetime,
            num_timestamps: int,
            step_length: timedelta,
    ) -> List[Tuple[datetime, Optional[int]]]:
        last_timestamp = first_timestamp + (num_timestamps-1) * step_length
        all_changelist_deployment_times = list(Deployment.objects
                                          .filter(environment=self.environment)
                                          .filter(status=Deployment.STATUS_PASS)
                                          .filter(time__gte=first_timestamp - self.checking_period)
                                          .filter(time__lt=last_timestamp)
                                          .order_by('change_list_id', 'time')
                                          .distinct('change_list_id')
                                          .only('change_list_id', 'time')
                                          .seal())
        all_changelist_times = list(ChangeList.objects
                               .filter(project_id=self.environment.project_id)
                               .filter(time__gte=first_timestamp - self.checking_period)
                               .filter(time__lt=last_timestamp)
                               .order_by('time')
                               .only('id', 'time')
                               .seal())
        all_changelists_count = len(all_changelist_times)
        all_changelist_deployments_count = len(all_changelist_deployment_times)
        self._warn_about_performance_if_operations_count_is_too_large(num_timestamps * (all_changelists_count + all_changelist_deployments_count))
        result: List[Tuple[datetime, Optional[int]]] = []
        for i in range(num_timestamps):
            current_dt = first_timestamp + i * step_length
            lead_time = self._compute_single_timestamp_avg_lead_time(all_changelist_deployment_times, all_changelist_times, current_dt)
            result.append((current_dt, lead_time))
        return result

    def _compute_single_timestamp_avg_lead_time(self, all_changelist_deployment_times, all_changelist_times, current_dt):
        checking_start_dt = current_dt - self.checking_period
        changelist_times = [c for c in all_changelist_times if checking_start_dt <= c.time < current_dt]
        deployment_times = {d.change_list_id: d.time
                       for d in all_changelist_deployment_times
                       if checking_start_dt <= d.time < current_dt}

        closest_passed_deployment_time_to_current_changelist = None
        total_lead_time = timedelta(0)
        lead_times_count = 0
        for change_list in reversed(changelist_times):
            first_passed_deployment_time_on_current_changelist = deployment_times.get(change_list.id)

            if closest_passed_deployment_time_to_current_changelist is None:
                closest_passed_deployment_time_to_current_changelist = first_passed_deployment_time_on_current_changelist

            an_earlier_deployment_exists = bool(
                first_passed_deployment_time_on_current_changelist is not None
                and first_passed_deployment_time_on_current_changelist < closest_passed_deployment_time_to_current_changelist
            )
            if an_earlier_deployment_exists:
                closest_passed_deployment_time_to_current_changelist = first_passed_deployment_time_on_current_changelist

            if closest_passed_deployment_time_to_current_changelist is None:
                continue

            total_lead_time += closest_passed_deployment_time_to_current_changelist - change_list.time
            lead_times_count += 1

        if lead_times_count == 0:
            return None

        return int(total_lead_time.total_seconds() / lead_times_count)
