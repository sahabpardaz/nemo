from rest_framework import viewsets, mixins
from rest_framework import filters
from apps.dashboard.serializers import UserProjectNotifSettingSerializer
from apps.dashboard.models import UserProjectNotifSetting
from apps.devops_metrics.constants import PROJECT_ID_URL_PARAMETER


class ProjectAccessFilter(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own projects.
    """
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(user=request.user)


class UserProjectNotifSettingViewSet(
        viewsets.GenericViewSet,
        mixins.UpdateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
    ):
    serializer_class = UserProjectNotifSettingSerializer
    lookup_field = 'project'
    queryset = UserProjectNotifSetting.objects.all()
    filter_backends = [ProjectAccessFilter]
    http_method_names = ['get', 'patch']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context[UserProjectNotifSettingSerializer.CONTEXT_KEY_PROJECT_ID] = self.kwargs.get(PROJECT_ID_URL_PARAMETER)
        context[UserProjectNotifSettingSerializer.CONTEXT_KEY_USER] = self.request.user
        return context
