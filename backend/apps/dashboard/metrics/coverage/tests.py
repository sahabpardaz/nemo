from abc import abstractmethod
import logging
from datetime import timedelta, datetime
from typing import Optional

from django.utils import timezone
from django.test import TestCase
from django.contrib.auth.models import User
from apps.dashboard.tests.utils import DjangoCurrentTimeMock

from apps.utils.general_utils import coalesce
from apps.dashboard.models import (
    MaturityModel,
    Project,
    CoverageReport,
)
from apps.dashboard.metrics.computation_test_base import ConsecutiveTimestampsMetricComputerTestingMixin
from apps.dashboard.metrics.coverage.computation import (
    CoverageMetricComputerBase,
    OverallCoverageComputer,
    IncrementalCoverageComputer,
)


logger = logging.getLogger(__name__)


class CoverageMetricComputingTestsBase(TestCase, ConsecutiveTimestampsMetricComputerTestingMixin[float]):

    # Override
    def setUp(self):
        maturity_model = MaturityModel.objects.create(name="test")
        self.user = User.objects.create(username="test")
        self.project = Project.objects.create(name="test", maturity_model=maturity_model, creator=self.user)
        self.now = timezone.make_aware(datetime(2000, 1, 1))

    @abstractmethod
    def get_computer_class(self):
        pass

    # Override
    def get_computer(self, checking_period_days: Optional[int] = None) -> CoverageMetricComputerBase:
        checking_period = None if checking_period_days is None else timedelta(days=checking_period_days)
        ComputerClass = self.get_computer_class()
        return ComputerClass(self.project, checking_period)

    @abstractmethod
    def coverage_type(self):
        pass

    def add_coverage_report(self, value: float, time: datetime, coverage_type=None, user=None, version="") -> CoverageReport:
        with DjangoCurrentTimeMock(time):
            return CoverageReport.objects.create(
                project=self.project,
                value=value,
                coverage_type=coalesce(coverage_type, self.coverage_type()),
                creator=user,
                version=version,
            )


class OverallCoverageComputingTests(CoverageMetricComputingTestsBase):

    # Override
    def get_computer_class(self):
        return OverallCoverageComputer

    # Override
    def coverage_type(self):
        return CoverageReport.TYPE_OVERALL

    def test_consistency_between_computation_of_single_and_consecutive_timestamps(self):
        self.add_coverage_report(0.1, self.now+timedelta(days=0, hours=20))
        self.add_coverage_report(0.2, self.now+timedelta(days=1, hours=14))
        self.add_coverage_report(0.3, self.now+timedelta(days=1, hours=23))
        self.add_coverage_report(0.4, self.now+timedelta(days=2, hours=1))
        self.add_coverage_report(0.5, self.now+timedelta(days=2, hours=22))
        self.add_coverage_report(0.6, self.now+timedelta(days=3, hours=2))
        self.check_all_combinations_of_consecutive_timestamps(
            first_timestamp=self.now,
            checking_period_days=1,
            expected_values=[
                None,
                0.1,
                0.3,
                0.5,
                0.6,
                None,
                None,
                None,
            ]
        )
        self.check_all_combinations_of_consecutive_timestamps(
            first_timestamp=self.now,
            checking_period_days=2,
            expected_values=[
                None,
                0.1,
                0.3,
                0.5,
                0.6,
                0.6,
                None,
                None,
            ]
        )
        self.check_all_combinations_of_consecutive_timestamps(
            first_timestamp=self.now,
            checking_period_days=3,
            expected_values=[
                None,
                0.1,
                0.3,
                0.5,
                0.6,
                0.6,
                0.6,
                None,
            ]
        )


class IncrementalCoverageComputingTests(CoverageMetricComputingTestsBase):

    # Override
    def get_computer_class(self):
        return IncrementalCoverageComputer

    # Override
    def coverage_type(self):
        return CoverageReport.TYPE_INCREMENTAL

    def test_consistency_between_computation_of_single_and_consecutive_timestamps(self):
        self.add_coverage_report(0.01, self.now+timedelta(days=0, hours=20))
        self.add_coverage_report(0.02, self.now+timedelta(days=1, hours=14))
        self.add_coverage_report(0.04, self.now+timedelta(days=1, hours=23))
        self.add_coverage_report(0.08, self.now+timedelta(days=2, hours=1))
        self.add_coverage_report(0.16, self.now+timedelta(days=2, hours=22))
        self.add_coverage_report(0.32, self.now+timedelta(days=3, hours=2))
        self.check_all_combinations_of_consecutive_timestamps(
            first_timestamp=self.now,
            checking_period_days=1,
            expected_values=[
                None,
                0.01/1,
                0.06/2,
                0.24/2,
                0.32/1,
                None,
                None,
                None,
            ]
        )
        self.check_all_combinations_of_consecutive_timestamps(
            first_timestamp=self.now,
            checking_period_days=2,
            expected_values=[
                None,
                0.01/1,
                0.07/3,
                0.30/4,
                0.56/3,
                0.32/1,
                None,
                None,
            ]
        )
        self.check_all_combinations_of_consecutive_timestamps(
            first_timestamp=self.now,
            checking_period_days=3,
            expected_values=[
                None,
                0.01/1,
                0.07/3,
                0.31/5,
                0.62/5,
                0.56/3,
                0.32/1,
                None,
            ]
        )
