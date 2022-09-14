import logging
from typing import List
from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from apps.dashboard.models import Project, Goal
from apps.devops_metrics.constants import PROJECT_ID_URL_PARAMETER
from apps.utils.group_and_permission_utils import get_related_add_permission_codename


logger = logging.getLogger(__name__)


class RelationalSpecialPermissionsBase(BasePermission):
    @property
    def methods(self):
        raise NotImplementedError

    @property
    def base_model(self):
        raise NotImplementedError

    @property
    def related_model(self):
        raise NotImplementedError

    @property
    def related_model_parameter_key(self):
        raise NotImplementedError

    def has_permission(self, request, view):
        if request.method in self.methods:
            try:
                required_related_model_permission = self._get_permissions_name(request)
            except PermissionError:
                return False

            if request.user.has_perms(required_related_model_permission):
                return True
            return False
        return True

    def _get_permissions_name(self, request) -> List[str]:
        raise NotImplementedError


class NestedModelsRelatedToBaseModelPermissions(BasePermission):
    """
    This Model use when you want let Nested objects of a specific model,
    can do any action if has access to base model permissions.
    For example:
        B, C are related to A with foreign key,
        This permission let user add object B or C if has permission to view object A.
    How To Use:
        You should just define permissions with some permissions in base model.
    """
    @property
    def permissions(self):
        raise NotImplementedError

    def get_base_model_obj(self, request):
        raise NotImplementedError

    def has_permission(self, request, view):
        """
        Just filled model_cls with base_model and no other changes made to method.
        """
        if not request.user:
            return False

        return request.user.has_perms(
            self.permissions,
            self.get_base_model_obj(request)
        )


class NestedModelsRelatedToProjectPermissions(NestedModelsRelatedToBaseModelPermissions):
    permissions = ['dashboard.view_project']

    def get_base_model_obj(self, request):
        request_url_parameters = request.resolver_match.kwargs
        if PROJECT_ID_URL_PARAMETER in request_url_parameters:
            project_id = int(request_url_parameters.get(PROJECT_ID_URL_PARAMETER))
        else:
            logger.error(
                f"Project id url parameter not found. "
                f"(request url parameters : {request_url_parameters})"
            )
            raise ValueError

        return get_object_or_404(Project, pk=project_id)


class AddGoalRelatedToProjectPermission(RelationalSpecialPermissionsBase):
    methods = ['POST']
    base_model = Goal
    related_model = Project
    related_model_parameter_key = PROJECT_ID_URL_PARAMETER

    def _get_permissions_name(self, request) -> List[str]:
        request_url_parameters = request.resolver_match.kwargs
        if self.related_model_parameter_key in request_url_parameters:
            base_model_object_pk = int(request_url_parameters.get(self.related_model_parameter_key))
        else:
            logger.debug(f"Related model primary key not found. (request url parameters : {request_url_parameters})")
            raise PermissionError

        related_model_obj = get_object_or_404(self.related_model, pk=base_model_object_pk)
        related_add_permission_name = get_related_add_permission_codename(self.base_model, related_model_obj)
        try:
            required_related_model_permission = Permission.objects.get(
                codename=related_add_permission_name
            )
        except Permission.DoesNotExist:
            logger.exception(f"Permission {related_add_permission_name} not found.")
            raise PermissionError

        return [
            '.'.join([
                required_related_model_permission.content_type.app_label,
                required_related_model_permission.codename
            ]),
        ]
