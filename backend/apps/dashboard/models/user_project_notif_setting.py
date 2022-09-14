from django.db import models
from django.contrib.auth.models import User

from apps.dashboard.models.project import Project


class UserProjectNotifSetting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    receive_notifications = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='dashboard_userprojectnotifsetting_uk_user_and_project',
                fields=['user', 'project'],
            ),
        ]
