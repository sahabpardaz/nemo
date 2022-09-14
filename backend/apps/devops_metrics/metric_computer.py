import logging
from datetime import timedelta
from typing import Generic
from apps.dashboard.metrics.computation_base import TMetric, ConsecutiveTimestampsMetricComputerMixin
from apps.dashboard.models import Environment


logger = logging.getLogger(__name__)


class MetricComputer(Generic[TMetric], ConsecutiveTimestampsMetricComputerMixin[TMetric]):

    def __init__(self, environment: Environment, checking_period: timedelta):
        self.environment = environment
        self.checking_period = checking_period
