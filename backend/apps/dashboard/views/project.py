import logging
from datetime import timedelta
from rest_framework import filters, viewsets, mixins
from rest_framework.decorators import permission_classes, action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import DjangoObjectPermissions
from rest_framework_guardian.filters import ObjectPermissionsFilter
from apps.dashboard.models.evaluation import EvaluationReport
from apps.dashboard.models.maturity_model import MaturityModelItem
from apps.dashboard.item_retrieve_utils import get_project_maturity_item_state
from apps.dashboard.models import (
    EvaluationRequest,
    Project,
    Goal,
    SonarProject,
    GitlabProject,
    CoverageReport
)
from apps.dashboard.permissions import AddGoalRelatedToProjectPermission, \
    NestedModelsRelatedToProjectPermissions
from apps.dashboard.serializers import (
    EvaluationReportSerializer, EvaluationRequestSerializer, ProjectAPITokenSerializer, ProjectMaturityStateSerializer,
    ProjectSerializer,
    GoalSerializer,
    SonarProjectSerializer,
    GitlabProjectSerializer,
    ProjectMaturityStateParametersSerializer, ProjectMaturityItemStateSerializer,
)
from apps.dashboard.project_retrieve_utils import (
    get_project_maturity_state,
    get_project_with_related_fields,
    incremental_coverage_items_disabled,
    overall_coverage_items_disabled,
    hit_visit_for_project,
)
from apps.dashboard.metrics.coverage.computation import (
    OverallCoverageComputer,
    IncrementalCoverageComputer,
)
from apps.devops_metrics.constants import PROJECT_ID_URL_PARAMETER
from apps.devops_metrics.serializers import DailyMetricReportRequestParametersSerializer

logger = logging.getLogger(__name__)


@permission_classes((NestedModelsRelatedToProjectPermissions,))
class EvaluationRequestViewSet(viewsets.ModelViewSet):
    serializer_class = EvaluationRequestSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return EvaluationRequest.objects \
            .filter(project_id=self.kwargs[PROJECT_ID_URL_PARAMETER])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project_id'] = self.kwargs.get(PROJECT_ID_URL_PARAMETER)
        context['user'] = self.request.user
        return context

    def destroy(self, request, *args, **kwargs):
        self.serializer_class.validate_on_delete(self.get_object())
        return super().destroy(request, *args, **kwargs)


# AddGoalRelatedToProjectPermission
@permission_classes((DjangoObjectPermissions, AddGoalRelatedToProjectPermission))
class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    filter_backends = [ObjectPermissionsFilter]

    def get_queryset(self):
        return Goal.objects \
            .filter(project_id=self.kwargs[PROJECT_ID_URL_PARAMETER])


@permission_classes((DjangoObjectPermissions,))
class ProjectViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = ProjectSerializer
    filter_backends = [ObjectPermissionsFilter]

    def get_queryset(self):
        return Project.objects.all()

    def retrieve(self, request, *args, **kwargs):
        hit_visit_for_project(
            request=request,
            project=self.get_object(),
        )
        return super().retrieve(request, *args, *kwargs)

    @action(detail=True, url_path="maturity-state", name="project-maturity-state")
    def project_maturity_state(self, request, *args, **kwargs):
        project = get_project_with_related_fields(self.get_object().pk)
        parameters_serializer = ProjectMaturityStateParametersSerializer(data=request.query_params)
        parameters_serializer.is_valid(raise_exception=True)
        snapshot_time = parameters_serializer.validated_data.get('snapshot_time')
        maturity_state = get_project_maturity_state(project, current_time=snapshot_time)
        return Response(ProjectMaturityStateSerializer(instance=maturity_state).data)

    @action(detail=True, url_path="maturity-item-state/(?P<item_id>\d+)", name="project-maturity-item-state")
    def project_maturity_item_state(self, request, item_id, *args, **kwargs):
        parameters_serializer = ProjectMaturityStateParametersSerializer(data=request.query_params)
        parameters_serializer.is_valid(raise_exception=True)
        project = self.get_object()
        item = MaturityModelItem.objects.filter(pk=item_id).first()
        if item is None:
            raise ValidationError("Item not found!")
        snapshot_time = parameters_serializer.validated_data.get('snapshot_time')
        item_state = get_project_maturity_item_state(item, project, snapshot_time)
        return Response(ProjectMaturityItemStateSerializer(instance=item_state).data)

    @action(detail=True, url_path="metric/overall-coverage", name="overall-coverage")
    def overall_coverage_metric(self, request, *args, **kwargs):
        project = self.get_object()
        if not overall_coverage_items_disabled(project):
            value = CoverageReport.compute_overall_coverage(project_id=project.id)
        else:
            value = None
        return Response({'value': value})

    @action(detail=True, url_path="metric/incremental-coverage", name="incremental-coverage")
    def incremental_coverage_metric(self, request, *args, **kwargs):
        project = self.get_object()
        if not incremental_coverage_items_disabled(project):
            value = CoverageReport.compute_incremental_coverage(project_id=project.id)
        else:
            value = None
        return Response({'value': value})

    @action(detail=True, url_path="graphs/daily-coverage", name="daily-coverage-graph")
    def daily_coverage_graph(self, request, *args, **kwargs):
        project = self.get_object()
        daily_metric_parameters_parser = DailyMetricReportRequestParametersSerializer(data=request.query_params)
        daily_metric_parameters_parser.is_valid(raise_exception=True)
        parsed_parameters = daily_metric_parameters_parser.validated_data
        checking_period = timedelta(days=parsed_parameters['checking_period_days'])
        first_date = parsed_parameters['period_start_date']
        last_date = parsed_parameters['period_end_date']
        overall_coverage_computer = OverallCoverageComputer(project, checking_period)
        incremental_coverage_computer = IncrementalCoverageComputer(project, checking_period)
        overall_coverage_data = overall_coverage_computer.get_daily_graph_data_serialized(first_date, last_date)
        incremental_coverage_data = incremental_coverage_computer.get_daily_graph_data_serialized(first_date, last_date)
        return Response({
            "overall": overall_coverage_data,
            "incremental": incremental_coverage_data,
        })

    @action(detail=True, url_path="api-token", name="api-token")
    def api_token(self, request, *args, **kwargs):
        project = self.get_object()
        return Response(ProjectAPITokenSerializer(project.auth_token).data)


@permission_classes((NestedModelsRelatedToProjectPermissions,))
class SonarProjectViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SonarProjectSerializer

    def get_queryset(self):
        return SonarProject.objects \
            .filter(nemo_project=self.kwargs[PROJECT_ID_URL_PARAMETER])


@permission_classes((NestedModelsRelatedToProjectPermissions,))
class GitlabProjectViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = GitlabProjectSerializer

    def get_queryset(self):
        return GitlabProject.objects \
            .filter(nemo_project=self.kwargs[PROJECT_ID_URL_PARAMETER])


class EvaluationReportViewSet(viewsets.ReadOnlyModelViewSet):
    URL_PARAM_MM_ITEM_ID = 'mm_item_id'

    serializer_class = EvaluationReportSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['latest_evaluation_time']
    ordering = ['-latest_evaluation_time']

    def get_queryset(self):
        return EvaluationReport.objects \
            .filter(project=self.kwargs[PROJECT_ID_URL_PARAMETER]) \
            .filter(maturity_model_item=self.kwargs[EvaluationReportViewSet.URL_PARAM_MM_ITEM_ID])
