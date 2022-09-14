import logging
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.utils.group_and_permission_utils import (
    get_related_add_permission_codename,
    get_product_managers_of_project_group_name,
    get_developers_of_project_group_name,
    get_team_leaders_of_project_group_name,
    set_model_permissions_over_model,
    set_object_permissions_over_queryset_or_objects,
    get_quality_committee_group_name,
)
from apps.dashboard.models import (
    Project,
    Goal,
)


logger = logging.getLogger(__name__)

def create_project_groups_and_assign_permissions(instance: Project):
    create_project_groups(instance)
    assign_permissions_to_project_groups(instance)


def create_project_groups(instance: Project):
    Group.objects.get_or_create(
        name=get_product_managers_of_project_group_name(instance.name)
    )
    Group.objects.get_or_create(
        name=get_developers_of_project_group_name(instance.name)
    )
    Group.objects.get_or_create(
        name=get_team_leaders_of_project_group_name(instance.name)
    )


def delete_project_groups(instance: Project):
    Group.objects.filter(
        name=get_product_managers_of_project_group_name(instance.name)
    ).delete()
    Group.objects.filter(
        name=get_developers_of_project_group_name(instance.name)
    ).delete()
    Group.objects.filter(
        name=get_team_leaders_of_project_group_name(instance.name)
    ).delete()


def assign_permissions_to_project_groups(instance: Project):
    product_managers = Group.objects.get(
        name=get_product_managers_of_project_group_name(instance.name)
    )
    developers = Group.objects.get(
        name=get_developers_of_project_group_name(instance.name)
    )
    team_leaders = Group.objects.get(
        name=get_team_leaders_of_project_group_name(instance.name)
    )
    quality_committee = Group.objects.get(
        name=get_quality_committee_group_name()
    )

    set_model_permissions_over_model(
        permissions=[
            'add_goal',
            'view_goal',
            'change_goal',
            'delete_goal',
        ],
        model=Goal,
        union_of_users_and_groups=[product_managers]
    )

    set_model_permissions_over_model(
        permissions=[
            'view_goal',
        ],
        model=Goal,
        union_of_users_and_groups=[
            developers,
            team_leaders,
        ]
    )

    set_model_permissions_over_model(
        permissions=[
            'view_project',
        ],
        model=Project,
        union_of_users_and_groups=[
            product_managers,
            developers,
            team_leaders,
        ]
    )

    set_object_permissions_over_queryset_or_objects(
        permissions=[
            'view_project',
        ],
        queryset_or_objects=[instance],
        union_of_users_and_groups=[
            product_managers,
            developers,
            team_leaders,
            quality_committee,
        ]
    )

    set_object_permissions_over_queryset_or_objects(
        permissions=[
            'change_project',
            'delete_project',
        ],
        queryset_or_objects=[instance],
        union_of_users_and_groups=[
            quality_committee,
        ]
    )

    # Create relative permission to add goal for this project
    content_type = ContentType.objects.get_for_model(instance)
    permission_codename = get_related_add_permission_codename(Goal, instance)
    try:
        permission = Permission.objects.get(
            codename=permission_codename,
            content_type=content_type
        )
    except Permission.DoesNotExist:
        permission = Permission.objects.create(
            codename=permission_codename,
            name=f'Can create goal for project {instance.name} [{instance.pk}]',
            content_type=content_type
        )

    if not permission:
        logger.error(f"Couldn't get or create permission {permission_codename}.")

    set_model_permissions_over_model(
        permissions=[
            permission.codename,
        ],
        model=Project,
        union_of_users_and_groups=[
            product_managers,
        ]
    )


def assign_permissions_to_groups_after_goal_created(instance: Goal):
    product_managers = Group.objects.get(
        name=get_product_managers_of_project_group_name(instance.project.name)
    )
    developers = Group.objects.get(
        name=get_developers_of_project_group_name(instance.project.name)
    )
    team_leaders = Group.objects.get(
        name=get_team_leaders_of_project_group_name(instance.project.name)
    )
    quality_committee = Group.objects.get(
        name=get_quality_committee_group_name()
    )

    set_object_permissions_over_queryset_or_objects(
        permissions=[
            'view_goal',
        ],
        queryset_or_objects=[instance],
        union_of_users_and_groups=[
            product_managers,
            developers,
            team_leaders,
            quality_committee,
        ]
    )

    set_object_permissions_over_queryset_or_objects(
        permissions=[
            'change_goal',
            'delete_goal',
        ],
        queryset_or_objects=[instance],
        union_of_users_and_groups=[
            product_managers,
        ]
    )


def rename_project_groups(old_project_name: str, new_project_name: str):
    if old_project_name == new_project_name:
        return

    for get_group_name in (
        get_product_managers_of_project_group_name,
        get_developers_of_project_group_name,
        get_team_leaders_of_project_group_name,
    ):
        group = Group.objects.get(name=get_group_name(old_project_name))
        group.name = get_group_name(new_project_name)
        group.save()
