from django.db.models.signals import pre_save
from django.dispatch import receiver
from guardian.shortcuts import UserObjectPermission
from apps.dashboard.signals._shared_utils import raise_error_for_direct_user_permission_assignment

@receiver(pre_save, sender=UserObjectPermission)
def on_user_object_permission_pre_save(**kwargs) -> None:
    raise_error_for_direct_user_permission_assignment()
