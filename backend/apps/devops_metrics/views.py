import logging
from datetime import timedelta
from typing import Type
from django.utils import timezone
from rest_condition import Or
from rest_framework import viewsets, mixins
from rest_framework.decorators import permission_classes, action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from apps.dashboard.models import Project, Environment
from apps.dashboard.permissions import NestedModelsRelatedToProjectPermissions
from apps.devops_metrics.constants import (
    PROJECT_ID_URL_PARAMETER,
    DEPLOYMENT_NOT_ENOUGH,
    KEY_CHANGE_FAILURE_RATE,
    KEY_TIME_TO_RESTORE,
    KEY_LEAD_TIME,
    KEY_DEPLOYMENT_FREQUENCY,
    DEFAULT_CHECKING_PERIOD_DAYS)
from apps.devops_metrics.change_failure_rate.computation import ChangeFailureRateComputer
from apps.devops_metrics.deployment_frequency.computation import DeploymentFrequencyComputer
from apps.devops_metrics.time_to_restore.computation import TimeToRestoreComputer
from apps.devops_metrics.lead_time.computation import LeadTimeComputer
from apps.devops_metrics.filters import EnvironmentThroughProjectFilterBackend
from apps.devops_metrics.metric_computer import MetricComputer
from apps.devops_metrics.models import ChangeList, \
    Deployment, ServiceStatusReport
from apps.devops_metrics.permissions import ApiProjectTokenPermission, \
    NestedApiProjectTokenPermission
from apps.devops_metrics.serializers import (
    ProjectSerializer,
    ChangeListSerializer,
    DeploymentSerializer,
    ServiceStatusReportSerializer,
    DailyMetricReportRequestParametersSerializer)
from apps.dashboard.serializers import EnvironmentSerializer
from apps.utils import general_utils

logger = logging.getLogger(__name__)


@permission_classes((Or(ApiProjectTokenPermission, NestedModelsRelatedToProjectPermissions),))
class ProjectViewSet(NestedViewSetMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


@permission_classes((Or(NestedApiProjectTokenPermission, NestedModelsRelatedToProjectPermissions),))
class EnvironmentViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer

    @action(detail=True)
    def statistics(self, request, *args, **kwargs):
        checking_period_days = request.query_params.get('checking_period_days')
        if checking_period_days is None:
            checking_period = timedelta(days=DEFAULT_CHECKING_PERIOD_DAYS)
        else:
            checking_period = timedelta(days=int(checking_period_days))

        environment = self.get_object()
        now = timezone.now()

        def compute_for_now(computer_cls: Type[MetricComputer]):
            computer = computer_cls(environment, checking_period)
            return computer.compute_for_single_timestamp(now)
        data = {
            KEY_DEPLOYMENT_FREQUENCY: str(general_utils.coalesce(compute_for_now(DeploymentFrequencyComputer), DEPLOYMENT_NOT_ENOUGH)),
            KEY_LEAD_TIME: str(general_utils.coalesce(compute_for_now(LeadTimeComputer), DEPLOYMENT_NOT_ENOUGH)),
            KEY_TIME_TO_RESTORE: str(general_utils.coalesce(compute_for_now(TimeToRestoreComputer), DEPLOYMENT_NOT_ENOUGH)),
            KEY_CHANGE_FAILURE_RATE: str(general_utils.coalesce(compute_for_now(ChangeFailureRateComputer), DEPLOYMENT_NOT_ENOUGH)),
        }
        return Response(data)

    def handle_daily_metric(self, metric_computer_cls: Type[MetricComputer], parameters):
        environment = self.get_object()
        daily_metric_parameters_parser = DailyMetricReportRequestParametersSerializer(data=parameters)
        daily_metric_parameters_parser.is_valid(raise_exception=True)
        parsed_parameters = daily_metric_parameters_parser.validated_data
        metric_computer = metric_computer_cls(environment, timedelta(days=parsed_parameters['checking_period_days']))
        data = metric_computer.get_daily_graph_data_serialized(parsed_parameters['period_start_date'], parsed_parameters['period_end_date'])
        return Response(data)

    @action(detail=True, url_path="metric/change-failure-rate", name="daily-change-failure-rate")
    def daily_change_failure_rate(self, request, *args, **kwargs):
        return self.handle_daily_metric(
            metric_computer_cls=ChangeFailureRateComputer,
            parameters=request.query_params,
        )

    @action(detail=True, url_path="metric/lead-time", name="daily-lead-time")
    def daily_lead_time(self, request, *args, **kwargs):
        return self.handle_daily_metric(
            metric_computer_cls=LeadTimeComputer,
            parameters=request.query_params,
        )

    @action(detail=True, url_path="metric/deployment-frequency", name="daily-deployment-frequency")
    def daily_deployment_frequency(self, request, *args, **kwargs):
        return self.handle_daily_metric(
            metric_computer_cls=DeploymentFrequencyComputer,
            parameters=request.query_params,
        )

    @action(detail=True, url_path="metric/time-to-restore", name="daily-time-to-restore")
    def daily_time_to_restore(self, request, *args, **kwargs):
        return self.handle_daily_metric(
            metric_computer_cls=TimeToRestoreComputer,
            parameters=request.query_params,
        )


@permission_classes((Or(NestedApiProjectTokenPermission, NestedModelsRelatedToProjectPermissions),))
class ChangeListViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = ChangeList.objects.all()
    serializer_class = ChangeListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project_id'] = self.kwargs.get(PROJECT_ID_URL_PARAMETER)
        return context


@permission_classes((Or(NestedApiProjectTokenPermission, NestedModelsRelatedToProjectPermissions),))
class DeploymentViewSet(viewsets.ModelViewSet):
    queryset = Deployment.objects.all()
    serializer_class = DeploymentSerializer
    filter_backends = [EnvironmentThroughProjectFilterBackend]


@permission_classes((Or(NestedApiProjectTokenPermission, NestedModelsRelatedToProjectPermissions),))
class ServiceStatusReportViewSet(viewsets.ModelViewSet):
    queryset = ServiceStatusReport.objects.all()
    serializer_class = ServiceStatusReportSerializer
    filter_backends = [EnvironmentThroughProjectFilterBackend]
