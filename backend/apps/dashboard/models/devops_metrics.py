from django.db import models
from apps.dashboard.models.project import Project


class Environment(models.Model):
    NAME_MAX_LENGTH = 500
    DESCRIPTION_MAX_LENGTH = 500

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='environments',
    )
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    description = models.CharField(
        max_length=DESCRIPTION_MAX_LENGTH,
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='dashboard_environment_uk_project_and_name',
                fields=['project', 'name'],
            ),
        ]

    def is_default_in_project(self):
        return getattr(self, 'project_as_default_environment', None) is not None

    is_default_in_project.short_description = 'Default'
    is_default_in_project.boolean = True

    def __str__(self):
        return f'{self.project.name}-{self.name}'
