import logging
from typing import List, Optional, Union, Type
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import Group, Permission, User
from django.db.models import QuerySet
from guardian.shortcuts import assign_perm


ROLE_PRODUCT_MANAGER = "Product Managers"
ROLE_DEVELOPER = "Developers"
ROLE_TEAM_LEADER = "Team Leaders"
PATTERN_ROLE_POSTFIX = " [{role}]"
PATTERN_GROUP_NAME = f"{{project_name}}{PATTERN_ROLE_POSTFIX}"

logger = logging.getLogger(__name__)


def get_related_add_permission_codename(model, related_model_obj):
    return (
        f'add_{str(model.__name__.lower())}'
        f'_for_{related_model_obj.__class__.__name__.lower()}'
        f'_pk_{related_model_obj.pk}'
    )


def get_product_managers_of_project_group_name(project_name):
    return PATTERN_GROUP_NAME.format(project_name=project_name, role=ROLE_PRODUCT_MANAGER)


def get_developers_of_project_group_name(project_name):
    return PATTERN_GROUP_NAME.format(project_name=project_name, role=ROLE_DEVELOPER)


def get_team_leaders_of_project_group_name(project_name):
    return PATTERN_GROUP_NAME.format(project_name=project_name, role=ROLE_TEAM_LEADER)


def _get_role_postfix(role_name: str) -> str:
    return PATTERN_ROLE_POSTFIX.format(role=role_name)


def get_quality_committee_group_name():
    return 'Quality Committee'


def get_project_name_from_group_name(group_name: str) -> Optional[str]:
    """Get the project name (if any) from a given group name.

    Args:
        group_name (str):

    Returns:
        Optional[str]: The name of project if any, or None.
    """
    product_manager_postfix = _get_role_postfix(ROLE_PRODUCT_MANAGER)
    developer_postfix = _get_role_postfix(ROLE_DEVELOPER)
    team_leader_postfix = _get_role_postfix(ROLE_TEAM_LEADER)
    if group_name.endswith(product_manager_postfix):
        return group_name[:-len(product_manager_postfix)]
    elif group_name.endswith(developer_postfix):
        return group_name[:-len(developer_postfix)]
    elif group_name.endswith(team_leader_postfix):
        return group_name[:-len(team_leader_postfix)]
    else:
        return None


def set_object_permissions_over_queryset_or_objects(
    permissions: List[str],
    queryset_or_objects: Union[QuerySet, List[models.Model]],
    union_of_users_and_groups: List[Union[User, Group]]
):
    for obj in queryset_or_objects:
        for permission in permissions:
            for user_or_group in union_of_users_and_groups:
                assign_perm(permission, user_or_group, obj)


def set_model_permissions_over_model(
    permissions: List[str],
    model: Type[models.Model],
    union_of_users_and_groups: List[Union[User, Group]]
):
    model_content_type = ContentType.objects.get_for_model(
        model=model
    )
    for permission in permissions:
        permission, _ = Permission.objects.get_or_create(
            codename=permission,
            content_type=model_content_type
        )
        for user_or_group in union_of_users_and_groups:
            if hasattr(user_or_group, 'permissions'):
                user_or_group.permissions.add(permission)
            elif hasattr(user_or_group, 'user_permissions'):
                user_or_group.user_permissions.add(permission)
