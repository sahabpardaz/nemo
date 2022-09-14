from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.dashboard.models import Project, ProjectAPIToken, GitlabProject
from apps.dashboard.groups_and_permissions_handler import (
    create_project_groups_and_assign_permissions,
    delete_project_groups,
    rename_project_groups,
)


@receiver(post_save, sender=Project)
def on_project_post_save(instance, created, **kwargs):
    if created:
        create_project_groups_and_assign_permissions(instance)
    else:
        if not instance.tracker.has_changed('name'):
            return
        old_project_name = instance.tracker.previous('name')
        rename_project_groups(old_project_name, instance.name)


@receiver(post_delete, sender=Project)
def handle_permissions_and_groups_deletation(instance, *args, **kwargs):
    delete_project_groups(instance)


@receiver(post_save, sender=Project)
def create_token(sender, instance, created, **kwargs):
    if created:
        ProjectAPIToken.objects.create(project=instance)


@receiver(post_save, sender=Project)
def create_version_control_settings_after_project_created(instance, created, **kwargs):
    if created:
        GitlabProject.objects.create(nemo_project=instance)
