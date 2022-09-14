import logging
from abc import ABC, abstractmethod
from datetime import timedelta
from django.utils import timezone
from apps.dashboard.evaluators.base import Evaluator
from apps.dashboard.evaluators.registry import register
from apps.dashboard.models import (
    EvaluationType,
    EvaluationReport,
    CoverageReport,
)
from apps.dashboard.data_collectors.sonar_test_coverage import OverallTestCoverageCollector


logger = logging.getLogger(__name__)


class TestCoverageEvaluatorBase(Evaluator, ABC):
    @abstractmethod
    def _get_coverage_value(self, project_id, maturity_model_item):
        pass

    def evaluate(self, project, maturity_model_item):
        coverage_value = self._get_coverage_value(project.id, maturity_model_item)
        if coverage_value is None:
            return None
        acceptable_value = float(maturity_model_item.acceptable_value)
        status = EvaluationReport.STATUS_PASS if coverage_value >= acceptable_value else EvaluationReport.STATUS_FAIL
        evaluation_report = EvaluationReport.create_new(
            project=project,
            maturity_model_item=maturity_model_item,
            status=status,
            current_value=str(coverage_value),
        )
        return evaluation_report


@register(evaluation_kinds=[EvaluationType.KIND_TEST_COVERAGE])
class OverallTestCoverageEvaluator(TestCoverageEvaluatorBase):
    def _get_coverage_value(self, project_id, maturity_model_item):
        earliest_valid_time = timezone.now() - timedelta(days=maturity_model_item.evaluation_type.checking_period_days)
        return CoverageReport.compute_overall_coverage(
            project_id=project_id,
            gte_specific_date=earliest_valid_time.date(),
        )


@register(evaluation_kinds=[EvaluationType.KIND_INCREMENTAL_TEST_COVERAGE])
class IncrementalTestCoverageEvaluator(TestCoverageEvaluatorBase):
    def _get_coverage_value(self, project_id, maturity_model_item):
        earliest_valid_time = timezone.now() - timedelta(days=maturity_model_item.evaluation_type.checking_period_days)
        return CoverageReport.compute_incremental_coverage(
            project_id=project_id,
            gte_specific_date=earliest_valid_time.date(),
        )


@register(evaluation_kinds=[EvaluationType.KIND_IS_TEST_COVERAGE_CALCULATED])
class IsTestCoverageCalculatedEvaluator(Evaluator):
    def __init__(self):
        self.coverageCollector = OverallTestCoverageCollector()

    def evaluate(self, project, maturity_model_item):
        try:
            passed_report = EvaluationReport.create_new(
                project=project,
                maturity_model_item=maturity_model_item,
                status=EvaluationReport.STATUS_PASS,
            )

            latest_coverage = CoverageReport.get_latest(project.id, CoverageReport.TYPE_OVERALL) \
                or CoverageReport.get_latest(project.id, CoverageReport.TYPE_INCREMENTAL)
            if latest_coverage is None:
                raise Exception('No coverage report found at all.')

            coverage_is_recent = latest_coverage.last_update_time >= timezone.now() - timedelta(days=maturity_model_item.evaluation_type.checking_period_days)
            if coverage_is_recent:
                passed_report.description = f'A recently reported coverage found within last {maturity_model_item.evaluation_type.checking_period_days} days.'
                return passed_report
            else:
                prev_eval_report = EvaluationReport.get_latest(project,
                                                               maturity_model_item)
                if prev_eval_report is None:
                    raise Exception('Neither recent coverage report, nor previous evaluation report found.')
                if prev_eval_report.status == EvaluationReport.STATUS_FAIL:
                    raise Exception('No recent coverage reports found and the previous evaluation status is Failed.')
                prev_eval_report_is_still_valid = prev_eval_report.last_update_time >= timezone.now() - timedelta(days=maturity_model_item.evaluation_type.validity_period_days)
                if prev_eval_report_is_still_valid:
                    return None # Neither Pass nor Fail. Let the previous evaluation report be valid.
                else:
                    raise Exception('No recent coverage reports or evaluation reports found.')

        except Exception as e:
            return EvaluationReport.create_new(
                project=project,
                maturity_model_item=maturity_model_item,
                status=EvaluationReport.STATUS_FAIL,
                description=f'Exception: {str(e)}'
            )
