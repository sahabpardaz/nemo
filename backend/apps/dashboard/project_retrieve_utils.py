import logging
from datetime import datetime
from typing import Dict, Iterable, Tuple, Optional
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from django.db.models import F, QuerySet
from django.utils import timezone
from apps.dashboard.models.project_maturity_state import ProjectMaturityItemState, ProjectMaturityLevelState, ProjectMaturityState
from apps.dashboard.models import (
    EvaluationReport,
    Goal,
    EvaluationType,
    MaturityModelItemToggleRequest,
    Project,
    CoverageReport,
    MaturityModelItem,
    EvaluationRequest,
)

logger = logging.getLogger(__name__)

FAIL_STATUS = "Fail"
PASS_STATUS = "Pass"

ITEM_FAIL_REASON_NO_EVALUATION_REPORT_FOUND = "Not evaluated yet"
ITEM_FAIL_REASON_OUT_OF_VALIDITY_PERIOD = "Latest passed evaluation is expired, due to the validity period"
ITEM_FAIL_REASON_LAST_EVALUATION_FAILED = "Latest evaluation has marked the item as failed"


def get_project_maturity_state(project, current_time: datetime = None) -> ProjectMaturityState:
    if not current_time:
        current_time = timezone.now()

    latest_evaluation_report_finder = LatestEvaluationReportFinder(
        project=project,
        current_time=current_time,
    )
    latest_evaluation_report_finder.prefetch_latest_evaluation_reports_for_mm_items(project.maturity_model.items.values_list('id', flat=True))
    latest_approved_toggle_requests = get_latest_approved_toggle_requests(project, current_time)
    item_ids_with_pending_toggle_request = get_item_ids_with_pending_toggle_request(project)
    latest_pending_evaluation_requests = get_latest_pending_evaluation_requests(project)
    latest_pending_toggle_requests = get_latest_pending_toggle_requests(project)
    closest_goals = get_closest_goals(project, current_time)

    maturity_level_states = []
    for level in project.maturity_model.levels.all():
        maturity_item_states = []
        items = level.items
        for item in items.all():
            item_is_disabled = is_item_disabled(item.id, latest_approved_toggle_requests)
            item_state = ProjectMaturityItemState(
                item,
                is_disabled=item_is_disabled,
                latest_pending_evaluation_request_id=get_latest_pending_evaluation_request_id_for_item(item.id, latest_pending_evaluation_requests),
                latest_pending_toggle_request_id=get_latest_pending_toggle_request_id_for_item(item.id, latest_pending_toggle_requests),
            )
            if not item_is_disabled:
                latest_evaluation_report = latest_evaluation_report_finder.get_latest_evaluation_report_of_item(item.id)
                status, failure_reason = get_maturity_model_item_status(
                    maturity_model_item=item,
                    latest_evaluation_report=latest_evaluation_report,
                    current_time=current_time,
                )
                item_is_passed = status == PASS_STATUS
                closest_goal = get_closest_goal_of_item(item.id, closest_goals)
                item_state.is_passed = item_is_passed
                item_state.closest_goal = closest_goal

            maturity_item_states.append(item_state)

        maturity_level_states.append(ProjectMaturityLevelState(level, maturity_item_states))

    return ProjectMaturityState(project, maturity_level_states)


def get_latest_approved_toggle_requests(project, current_time: datetime = None) -> QuerySet:
    if current_time is None:
        current_time = timezone.now()

    return MaturityModelItemToggleRequest.objects \
        .filter(project=project) \
        .filter(approval__approved=True) \
        .filter(creation_time__lte=current_time) \
        .order_by('maturity_model_item_id', '-creation_time') \
        .distinct('maturity_model_item_id') \
        .only('maturity_model_item_id', 'disable') \
        .seal()


def is_item_disabled(item_id: int, latest_approved_toggle_requests: QuerySet) -> bool:
    for approved_toggle_request in latest_approved_toggle_requests:
        if approved_toggle_request.maturity_model_item_id == item_id:
            return approved_toggle_request.disable
    return False


class LatestEvaluationReportFinder:
    def __init__(self, project: Project, current_time: datetime, evaluation_reports_extra_fields: Iterable[str] = None):
        """
        Args:
            project (Project)
            current_time (datetime)
            evaluation_reports_extra_fields (Iterable[str], optional): A list of extra fields to be retrieved alongside the defaults. By default
                'maturity_model_item_id', 'status', 'creation_time', and 'latest_evaluation_time' fields are retrieved for each evaluation report.
                The other fields are ignored for performance optimization.
        """
        self.project = project
        self.current_time = current_time
        self.evaluation_reports_extra_fields = evaluation_reports_extra_fields
        if self.evaluation_reports_extra_fields is None:
            self.evaluation_reports_extra_fields = []

        self.latest_evaluation_reports_is_prefetched = False
        self.mm_item_ids_to_prefetch_latest_eval_reports_for: Iterable[int] = []
        self.prefetched_latest_evaluation_reports: Dict[int, EvaluationReport] = {}

    def get_latest_evaluation_report_of_item(self, item_id: int) -> Optional[EvaluationReport]:
        if self.latest_evaluation_reports_is_prefetched and item_id not in self.mm_item_ids_to_prefetch_latest_eval_reports_for:
            raise ValueError(
                "The given item id is not specified in the prefetched items. "
                "Please also specify the given id for prefetch, or don't prefetch any item at all. "
                f"(Prefetched item ids: {list(self.mm_item_ids_to_prefetch_latest_eval_reports_for)}, Given item id: {item_id})"
            )

        if self.latest_evaluation_reports_is_prefetched:
            return self.prefetched_latest_evaluation_reports.get(item_id)

        latest_evaluation_report_for_requested_item = self._get_latest_evaluation_reports([item_id]).values()
        if latest_evaluation_report_for_requested_item:
            return next(iter(latest_evaluation_report_for_requested_item))
        return None

    def prefetch_latest_evaluation_reports_for_mm_items(self, mm_item_ids: Iterable[int]):
        self.prefetched_latest_evaluation_reports = self._get_latest_evaluation_reports(mm_item_ids)
        self.mm_item_ids_to_prefetch_latest_eval_reports_for = mm_item_ids
        self.latest_evaluation_reports_is_prefetched = True

    def _get_latest_evaluation_reports(self, mm_item_ids: Iterable[int]) -> Dict[int, EvaluationReport]:
        latest_evaluation_reports_list = (EvaluationReport.objects
            .filter(project=self.project)
            .filter(creation_time__lte=self.current_time)
            .filter(maturity_model_item_id__in=mm_item_ids)
            .order_by('maturity_model_item_id', '-latest_evaluation_time', '-creation_time')
            .distinct('maturity_model_item_id')
            .only('maturity_model_item_id', 'status', 'creation_time', 'latest_evaluation_time', *self.evaluation_reports_extra_fields)
            .seal()
        )
        return {report.maturity_model_item_id:report for report in latest_evaluation_reports_list}


def get_closest_goals(project, current_time=timezone.now) -> QuerySet:
    return Goal.objects \
        .filter(project=project) \
        .filter(due_date__gt=current_time) \
        .annotate(maturity_model_item_id=F('maturity_model_items__id')) \
        .order_by('maturity_model_item_id', 'due_date') \
        .distinct('maturity_model_item_id')


def get_closest_goal_of_item(item_id: int, closest_goals: QuerySet) -> Goal:
    for goal in closest_goals:
        if item_id == goal.maturity_model_item_id:
            return goal
    return None


def get_item_ids_with_pending_toggle_request(project) -> QuerySet:
    return MaturityModelItemToggleRequest.objects \
        .filter(project=project) \
        .filter(approval__isnull=True) \
        .order_by('maturity_model_item_id') \
        .distinct('maturity_model_item_id') \
        .values_list('maturity_model_item_id', flat=True)


def get_latest_pending_evaluation_requests(project) -> QuerySet:
    return EvaluationRequest.objects \
        .filter(project=project) \
        .filter(status=EvaluationRequest.STATUS_PENDING) \
        .only('id', 'maturity_model_item_id') \
        .seal()


def get_latest_pending_toggle_requests(project) -> QuerySet:
    return MaturityModelItemToggleRequest.objects \
        .filter(project=project) \
        .filter(approval__isnull=True) \
        .only('id', 'maturity_model_item_id') \
        .seal()


def get_latest_pending_evaluation_request_id_for_item(item_id: int, latest_pending_evaluation_requests: QuerySet) -> Optional[int]:
    for evaluation_request in latest_pending_evaluation_requests:
        if evaluation_request.maturity_model_item_id == item_id:
            return evaluation_request.id
    return None


def get_latest_pending_toggle_request_id_for_item(item_id: int, latest_pending_toggle_requests: QuerySet) -> Optional[int]:
    for toggle_request in latest_pending_toggle_requests:
        if toggle_request.maturity_model_item_id == item_id:
            return toggle_request.id
    return None


def get_project_with_related_fields(project_pk) -> Project:
    """
        Returns project with pre-fetched related fields
        to reduce the number of database's queries we need later.
    """
    return Project.objects \
        .select_related('creator') \
        .select_related('default_environment') \
        .prefetch_related('maturity_model__levels__items__evaluation_type') \
        .get(pk=project_pk)


def incremental_coverage_items_disabled(project: Project):
    return _coverage_items_disabled(project, CoverageReport.TYPE_INCREMENTAL)


def overall_coverage_items_disabled(project: Project):
    return _coverage_items_disabled(project, CoverageReport.TYPE_OVERALL)


def _coverage_items_disabled(project: Project, coverage_type):
    coverage_type_to_evaluation_types = {
        CoverageReport.TYPE_OVERALL: EvaluationType.KIND_TEST_COVERAGE,
        CoverageReport.TYPE_INCREMENTAL: EvaluationType.KIND_INCREMENTAL_TEST_COVERAGE,
    }
    assert coverage_type in coverage_type_to_evaluation_types.keys(), \
        f"coverage_type argument should be one of these: {coverage_type_to_evaluation_types.keys()}"

    latest_approved_toggle_requests = get_latest_approved_toggle_requests(project)
    coverage_item_ids = project.maturity_model.items \
        .filter(evaluation_type__kind=coverage_type_to_evaluation_types.get(coverage_type)) \
        .values_list('id', flat=True)

    for coverage_item_id in coverage_item_ids:
        if not is_item_disabled(coverage_item_id, latest_approved_toggle_requests):
            return False
    return True


def get_maturity_model_item_status(maturity_model_item: MaturityModelItem, latest_evaluation_report: EvaluationReport, current_time: datetime) -> Tuple[str, Optional[str]]:
    """
        Returns status and fail reason. if status is pass returns none
    """
    if latest_evaluation_report is None:
        return FAIL_STATUS, ITEM_FAIL_REASON_NO_EVALUATION_REPORT_FOUND

    is_last_report_passed = latest_evaluation_report.status == EvaluationReport.STATUS_PASS

    if not is_last_report_passed:
        return FAIL_STATUS, ITEM_FAIL_REASON_LAST_EVALUATION_FAILED

    if not EvaluationReport.is_in_validity_period(latest_evaluation_report, maturity_model_item, current_time):
        return FAIL_STATUS, ITEM_FAIL_REASON_OUT_OF_VALIDITY_PERIOD

    return PASS_STATUS, None


def hit_visit_for_project(request, project):
    hit_count_obj = HitCount.objects.get_for_object(project)
    HitCountMixin.hit_count(request, hit_count_obj)
