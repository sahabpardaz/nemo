from rest_condition import Or
from rest_framework import viewsets, mixins
from rest_framework.decorators import permission_classes

from apps.dashboard.models.coverage_report import CoverageReport
from apps.dashboard.permissions import NestedModelsRelatedToProjectPermissions
from apps.dashboard.serializers import CoverageReportSerializer
from apps.devops_metrics.constants import PROJECT_ID_URL_PARAMETER
from apps.devops_metrics.permissions import NestedApiProjectTokenPermission


@permission_classes((Or(NestedApiProjectTokenPermission, NestedModelsRelatedToProjectPermissions),))
class CoverageReportViewSet(mixins.CreateModelMixin,
                            mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = CoverageReportSerializer

    def get_queryset(self):
        return CoverageReport.objects.filter(project_id=self.kwargs[PROJECT_ID_URL_PARAMETER])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project_id'] = self.kwargs.get(PROJECT_ID_URL_PARAMETER)
        context['user'] = self.request.user
        return context
