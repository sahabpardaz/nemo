from django.contrib.auth.models import Group
from django.db import migrations
from apps.utils.group_and_permission_utils import (
    set_model_permissions_over_model,
    set_object_permissions_over_queryset_or_objects,
)

QUALITY_COMMITTEE_GROUP_NAME = 'Quality Committee'


def init_quality_committee_group_with_permissions(apps, schema_editor):
    Project = apps.get_model("dashboard", "Project")
    Goal = apps.get_model("dashboard", "Goal")

    quality_committee, created = Group.objects.get_or_create(
        name=QUALITY_COMMITTEE_GROUP_NAME
    )

    set_model_permissions_over_model(
        permissions=[
            'view_project',
            'change_project',
            'add_project',
            'delete_project',
        ],
        model=Project,
        union_of_users_and_groups=[quality_committee]
    )

    set_model_permissions_over_model(
        permissions=[
            'view_goal',
        ],
        model=Goal,
        union_of_users_and_groups=[quality_committee]
    )

    set_object_permissions_over_queryset_or_objects(
        permissions=[
            'view_project',
            'change_project',
            'add_project',
            'delete_project',
        ],
        queryset_or_objects=Project.objects.all(),
        union_of_users_and_groups=[quality_committee]
    )

    set_object_permissions_over_queryset_or_objects(
        permissions=[
            'view_goal',
        ],
        queryset_or_objects=Goal.objects.all(),
        union_of_users_and_groups=[quality_committee]
    )


def delete_quality_committee_group(apps, schema_editor):
    Group.objects.filter(
        name=QUALITY_COMMITTEE_GROUP_NAME
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0001_initial'),
        ('guardian', '0002_generic_permissions_index'),
    ]

    operations = [
        migrations.RunPython(
            code=init_quality_committee_group_with_permissions,
            reverse_code=delete_quality_committee_group
        ),
    ]
