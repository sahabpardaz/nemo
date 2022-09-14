from django.shortcuts import get_object_or_404
from rest_framework import filters
from apps.dashboard.models import Project, Environment
from apps.devops_metrics.constants import (
    PROJECT_ID_URL_PARAMETER,
    ENVIRONMENT_ID_URL_PARAMETER,
)

class EnvironmentThroughProjectFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows objects when the given environment exists in the given project.
    """
    def filter_queryset(self, request, queryset, view):
        project = get_object_or_404(Project, pk=view.kwargs[PROJECT_ID_URL_PARAMETER])
        environment = get_object_or_404(Environment, pk=view.kwargs[ENVIRONMENT_ID_URL_PARAMETER], project=project)
        return queryset.filter(environment=environment)
