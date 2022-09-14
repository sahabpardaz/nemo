import logging
from django.conf import settings
from rest_framework.permissions import BasePermission
from apps.dashboard.models import Project
from apps.devops_metrics.constants import PROJECT_ID_URL_PARAMETER


logger = logging.getLogger(__name__)


class NestedApiProjectTokenPermission(BasePermission):
    """
    Permission class that can used in Project nested API endpoints and validate project access token
    Notice that "PARENT_LOOKUP_PROJECT" must be in parents_query_lookups of nested registers.
    """
    def has_permission(self, request, view):
        request_project_token = request.headers.get(settings.PROJECT_TOKEN_HEADER)
        request_url_parameters = request.resolver_match.kwargs

        if PROJECT_ID_URL_PARAMETER in request_url_parameters:
            project_id = int(request_url_parameters.get(PROJECT_ID_URL_PARAMETER))
        else:
            logger.debug(f"Project id url parameter not found. (request url parameters : {request_url_parameters})")
            return False

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            logger.debug(f"Project with id {project_id} not found.")
            return False

        if request_project_token == project.auth_token.key:
            return True
        else:
            logger.debug(f"Access token ({request_project_token}) is not valid for project {project_id}.")
            return False


class ApiProjectTokenPermission(BasePermission):
    """
    Permission class that can used in Project API endpoints and validate project access token
    """
    def has_object_permission(self, request, view, obj):
        request_project_token = request.headers.get(settings.PROJECT_TOKEN_HEADER)
        if isinstance(obj, Project):
            if request_project_token == obj.auth_token.key:
                return True
            else:
                logger.debug(f"Access token ({request_project_token}) is not valid for project {obj.id}.")
                return False
        else:
            logger.error(f"This permission class is not designed for non-project model endpoints")
            return False
