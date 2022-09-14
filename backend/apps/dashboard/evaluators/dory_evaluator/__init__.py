import logging
from typing import Optional, Tuple, List
from django.utils import timezone
from apps.dashboard.evaluators.base import Evaluator
from apps.dashboard.evaluators.registry import register
from apps.dashboard.models import (
    EvaluationType,
    DoryEvaluation,
    EvaluationReport,
    Project,
    MaturityModelItem
)
from apps.dashboard.models.dory import MaturityItemDoryResult

logger = logging.getLogger(__name__)


@register(evaluation_kinds=[EvaluationType.KIND_DORY])
class DoryEvaluator(Evaluator):
    def evaluate(self, project: Project, maturity_model_item: MaturityModelItem) -> Optional[EvaluationReport]:
        only_latest_dory_evaluation_should_be_considered = maturity_model_item.acceptable_value is None
        if only_latest_dory_evaluation_should_be_considered:
            return DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriod().evaluate(project, maturity_model_item)
        else:
            assert maturity_model_item.acceptable_value_type == MaturityModelItem.VALUE_TYPE_PERCENTAGE, (
                "Maturity items that are evaluated by Dory and has an 'acceptable_value', must have 'acceptable_value_type' of percentage. "
                f"Current acceptable_value_type: {maturity_model_item.acceptable_value_type}"
            )
            return DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriod().evaluate(project, maturity_model_item)


class DoryEvaluatorBasedOnLatestDoryEvaluationInCheckingPeriod(Evaluator):
    def evaluate(self, project: Project, maturity_model_item: MaturityModelItem) -> Optional[EvaluationReport]:
        current_time = timezone.now()
        dory_latest_completed_evaluation_in_checking_period = DoryEvaluation.get_completed_evaluations_in_checking_period(
            project=project,
            checking_period_days=maturity_model_item.evaluation_type.checking_period_days,
            current_time=current_time,
        ).last()

        if dory_latest_completed_evaluation_in_checking_period is None:
            return

        maturity_item_dory_result = dory_latest_completed_evaluation_in_checking_period.get_maturity_item_dory_result(item_code=maturity_model_item.code)
        if maturity_item_dory_result is None:
            return

        description = f"""Evaluated by latest dory evaluation in checking period
\tDory evaluation ID: {dory_latest_completed_evaluation_in_checking_period.id}
\tStatus: {'Passed' if maturity_item_dory_result.passed else 'Failed'}
        """

        return EvaluationReport.create_new(
            project=project,
            maturity_model_item=maturity_model_item,
            status=EvaluationReport.STATUS_PASS if maturity_item_dory_result.passed else EvaluationReport.STATUS_FAIL,
            description=description,
            creation_time=current_time,
            latest_evaluation_time=current_time,
        )


class DoryEvaluatorBasedOnAllDoryEvaluationsInCheckingPeriod(Evaluator):
    def evaluate(self, project: Project, maturity_model_item: MaturityModelItem) -> Optional[EvaluationReport]:
        current_time = timezone.now()
        dory_completed_evaluations_in_checking_period = DoryEvaluation.get_completed_evaluations_in_checking_period(
            project=project,
            checking_period_days=maturity_model_item.evaluation_type.checking_period_days,
            current_time=current_time,
        )
        passed_dory_evaluations_count = 0
        failed_dory_evaluations_count = 0
        dory_evaluation_id_to_maturity_item_dory_result_pairs: List[Tuple[int, MaturityItemDoryResult]] = []
        for dory_evaluation in dory_completed_evaluations_in_checking_period:
            maturity_item_dory_result = dory_evaluation.get_maturity_item_dory_result(item_code=maturity_model_item.code)
            if maturity_item_dory_result is None:
                continue

            if maturity_item_dory_result.passed:
                passed_dory_evaluations_count += 1
            else:
                failed_dory_evaluations_count += 1

            dory_evaluation_id_to_maturity_item_dory_result_pairs.append((dory_evaluation.id, maturity_item_dory_result))

        if passed_dory_evaluations_count == 0 and failed_dory_evaluations_count == 0:
            logger.info(f"No dory evaluations found in checking period for project {project.name}")
            return

        dory_evaluations_passed_percentage = (passed_dory_evaluations_count / (passed_dory_evaluations_count + failed_dory_evaluations_count)) * 100
        acceptable_passed_percentage = float(maturity_model_item.acceptable_value)
        item_is_passed = dory_evaluations_passed_percentage >= acceptable_passed_percentage

        return EvaluationReport.create_new(
            project=project,
            maturity_model_item=maturity_model_item,
            status=EvaluationReport.STATUS_PASS if item_is_passed else EvaluationReport.STATUS_FAIL,
            description=self._get_description(
                dory_evaluation_id_to_maturity_item_dory_result_pairs,
                passed_dory_evaluations_count,
                failed_dory_evaluations_count
            ),
            creation_time=current_time,
            latest_evaluation_time=current_time,
            current_value=str(dory_evaluations_passed_percentage),
        )

    def _get_description(self,
        dory_evaluation_id_to_maturity_item_dory_result_pairs: List[Tuple[int, MaturityItemDoryResult]],
        passed_dory_evaluations_count: int,
        failed_dory_evaluations_count: int,
    ):
        description_lines = []
        description_lines.append("Dory evaluations summary:")
        for dory_evaluation_id, maturity_item_dory_result in dory_evaluation_id_to_maturity_item_dory_result_pairs:
            description_lines.append(
                f"\tID: {dory_evaluation_id}, Status: {'Passed' if maturity_item_dory_result.passed else 'Failed'}"
            )
        description_lines.append("-" * 20)
        description_lines.append(f"Passed evaluations: {passed_dory_evaluations_count}, Failed evaluations: {failed_dory_evaluations_count}")
        return '\n'.join(description_lines)
