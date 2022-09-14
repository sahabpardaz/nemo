import json
import logging
from datetime import timedelta
import requests
from django.utils import timezone
from django.conf import settings
from apps.dashboard.evaluators.base import Evaluator
from apps.dashboard.evaluators.registry import register
from apps.dashboard.models import (
    EvaluationType,
    EvaluationReport,
)
from apps.devops_metrics.constants import DEPLOYMENT_NOT_ENOUGH
from apps.devops_metrics.lead_time.computation import LeadTimeComputer
from apps.devops_metrics.deployment_frequency.computation import DeploymentFrequencyComputer
from apps.devops_metrics.time_to_restore.computation import TimeToRestoreComputer
from apps.devops_metrics.change_failure_rate.computation import ChangeFailureRateComputer
from apps.devops_metrics.metric_computer import MetricComputer


logger = logging.getLogger(__name__)


class DevOpsMetricsBaseEvaluator(Evaluator):
    computer_class: MetricComputer

    def evaluate(self, project, maturity_model_item):
        value = self.__get_current_value_of_metric(
            default_environment=project.default_environment,
            maturity_model_item=maturity_model_item,
        )
        status = self.__get_status_from_current_value(
            current_value=value,
            expected_value=maturity_model_item.acceptable_value,
        )
        return EvaluationReport.create_new(
            project=project,
            maturity_model_item=maturity_model_item,
            status=status,
            current_value=value,
        )

    def __get_current_value_of_metric(self, default_environment, maturity_model_item):
        assert self.computer_class is not None and issubclass(self.computer_class, MetricComputer)

        computer = self.computer_class(
            environment=default_environment,
            checking_period=timedelta(days=maturity_model_item.evaluation_type.checking_period_days),
        )
        return computer.compute_for_single_timestamp(timezone.now())

    def __get_status_from_current_value(self, current_value, expected_value):
        if expected_value is None:
            raise ValueError("expected_value argument could not be None")

        if current_value is None:
            return EvaluationReport.STATUS_FAIL

        if current_value == DEPLOYMENT_NOT_ENOUGH:
            return EvaluationReport.STATUS_FAIL

        if int(float(current_value)) < int(float(expected_value)):
            return EvaluationReport.STATUS_PASS

        return EvaluationReport.STATUS_FAIL


@register(evaluation_kinds=[EvaluationType.KIND_LEAD_TIME])
class LeadTimeEvaluator(DevOpsMetricsBaseEvaluator):
    computer_class = LeadTimeComputer


@register(evaluation_kinds=[EvaluationType.KIND_TIME_TO_RESTORE])
class TimeToRestoreEvaluator(DevOpsMetricsBaseEvaluator):
    computer_class = TimeToRestoreComputer


@register(evaluation_kinds=[EvaluationType.KIND_DEPLOYMENT_FREQUENCY])
class DeploymentFrequencyEvaluator(DevOpsMetricsBaseEvaluator):
    computer_class = DeploymentFrequencyComputer


@register(evaluation_kinds=[EvaluationType.KIND_CHANGE_FAILURE_RATE])
class ChangeFailureRateEvaluator(DevOpsMetricsBaseEvaluator):
    computer_class = ChangeFailureRateComputer
