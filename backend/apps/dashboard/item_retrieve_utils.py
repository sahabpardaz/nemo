from datetime import datetime
from typing import Optional

from django.db.models import F

from apps.dashboard.models import (
    MaturityModelItem,
    Project, ProjectMaturityItemState
)
from apps.dashboard.models.evaluation import EvaluationReport, EvaluationRequest
from apps.dashboard.models.goal import Goal
from apps.dashboard.models.maturity_model import MaturityModelItemToggleRequest
from apps.dashboard.project_retrieve_utils import (
    PASS_STATUS,
    LatestEvaluationReportFinder,
    get_maturity_model_item_status,
)


def get_project_maturity_item_state(item: MaturityModelItem,
                                    project: Project,
                                    current_time: datetime) -> ProjectMaturityItemState:
    latest_evaluation_report: Optional[EvaluationReport] = LatestEvaluationReportFinder(
        project=project,
        current_time=current_time,
        evaluation_reports_extra_fields=['current_value', 'expected_value', 'value_type'],
    ).get_latest_evaluation_report_of_item(item.id)
    status, failure_reason = get_maturity_model_item_status(item, latest_evaluation_report, current_time)

    latest_pending_toggle_request = MaturityModelItemToggleRequest.get_latest_pending(item, project)

    closest_goal = Goal.objects \
        .filter(project=project) \
        .filter(due_date__gt=current_time) \
        .annotate(maturity_model_item_id=F('maturity_model_items__id')) \
        .filter(maturity_model_item_id=item.pk) \
        .order_by('due_date') \
        .first()

    return ProjectMaturityItemState(
        maturity_item=item,
        is_disabled=item.is_disabled(project, current_time),
        is_passed=status == PASS_STATUS,
        latest_evaluation_report=latest_evaluation_report,
        failure_reason=failure_reason,
        closest_goal=closest_goal,
        latest_pending_evaluation_request_id=get_latest_pending_evaluation_request_id(item, project),
        latest_pending_toggle_request_id=latest_pending_toggle_request.pk if latest_pending_toggle_request is not None else None,
    )


def get_latest_pending_evaluation_request_id(item: MaturityModelItem, project: Project) -> Optional[int]:
    eval_req = EvaluationRequest.get_latest_pending(item, project)
    return eval_req.pk if eval_req is not None else None
