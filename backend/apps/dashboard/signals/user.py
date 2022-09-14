from typing import Iterable
from django.contrib.auth.models import Group, User
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from guardian.shortcuts import get_objects_for_user
from apps.dashboard.models import UserProjectNotifSetting
from apps.dashboard.signals._shared_utils import raise_error_for_direct_user_permission_assignment


@receiver(m2m_changed, sender=User.groups.through)
def on_user_groups_changed(instance, reverse, action, pk_set, **kwargs) -> None:
    if reverse:
        _update_corresponding_notif_settings_of_group(instance, action, pk_set)
    else:
        _update_corresponding_notif_settings_of_user(user=instance)


def _update_corresponding_notif_settings_of_user(user: User) -> None:
    user_projects = get_objects_for_user(user, 'dashboard.view_project', accept_global_perms=False)
    for project in user_projects:
        UserProjectNotifSetting.objects.get_or_create(project=project, user=user)
    UserProjectNotifSetting.objects.filter(user=user) \
        .exclude(project__in=user_projects) \
        .delete()


def _update_corresponding_notif_settings_of_group(group: Group, action: str, pk_set: Iterable[int]):
    if action in ['post_add', 'post_remove']:
        users = User.objects.filter(id__in=pk_set)
    elif action == 'post_clear':
        # There seems no clean way of getting what's removed in this state!
        # https://stackoverflow.com/questions/69323987/django-m2m-changed-post-clear-get-cleared-objects
        users = User.objects.all()
    else:
        return
    for user in users:
        _update_corresponding_notif_settings_of_user(user)


@receiver(post_save, sender=User)
def on_user_post_save(instance: User, **kwargs) -> None:
    _update_corresponding_notif_settings_of_user(instance)


@receiver(m2m_changed, sender=User.user_permissions.through)
def on_user_permissions_changed(action: str, **kwargs) -> None:
    if action == 'pre_add':
        raise_error_for_direct_user_permission_assignment()
