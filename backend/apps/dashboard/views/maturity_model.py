from rest_framework import viewsets, mixins
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from apps.dashboard.permissions import NestedModelsRelatedToProjectPermissions
from apps.dashboard.serializers import MaturityModelSerializer, MaturityModelItemToggleRequestSerializer
from apps.dashboard.models import MaturityModel, MaturityModelItemToggleRequest
from apps.devops_metrics.constants import PROJECT_ID_URL_PARAMETER


class MaturityModelViewSet(mixins.CreateModelMixin,
                           mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = MaturityModelSerializer
    queryset = MaturityModel.objects.all()

    def get_permissions(self):
        if self.action == 'create':
            specified_permission_class = IsAdminUser
        else:
            specified_permission_class = IsAuthenticated
        return [specified_permission_class()]


@permission_classes((NestedModelsRelatedToProjectPermissions,))
class MaturityModelItemToggleRequestViewSet(viewsets.ModelViewSet):
    serializer_class = MaturityModelItemToggleRequestSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return MaturityModelItemToggleRequest.objects \
            .filter(project_id=self.kwargs[PROJECT_ID_URL_PARAMETER])

    def destroy(self, request, *args, **kwargs):
        self.serializer_class.validate_on_delete(self.get_object())
        return super().destroy(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project_id'] = self.kwargs.get(PROJECT_ID_URL_PARAMETER)
        context['user'] = self.request.user
        return context
