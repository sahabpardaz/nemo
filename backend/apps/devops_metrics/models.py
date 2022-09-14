from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin
from seal.models import SealableModel
from apps.dashboard.models import Project, Environment


NON_VALID_COMMIT_HASH = "Commit hash length must be 40"


def validate_commit_hash(value):
    if len(value) != 40:
        raise ValidationError(NON_VALID_COMMIT_HASH)


class ChangeList(ExportModelOperationsMixin('ChangeList'), SealableModel):
    COMMIT_HASH_MAX_LENGTH = 40
    CHANGE_LIST_ID_MAX_LENGTH = 100
    TITLE_MAX_LENGTH = 500

    # id (the default pk field) is considered to always be an auto-incrementing field for this model;
    # since it's used in changelist collection logic.
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=TITLE_MAX_LENGTH,
        null=True,
        blank=True,
    )
    commit_hash = models.CharField(
        validators=[validate_commit_hash],
        null=False,
        max_length=COMMIT_HASH_MAX_LENGTH,
        blank=False
    )
    time = models.DateTimeField(default=timezone.now, blank=True)
    change_list_id = models.CharField(
        null=False,
        blank=False,
        max_length=CHANGE_LIST_ID_MAX_LENGTH,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'change_list_id'], name='unique_change_list_id_in_project'),
            models.UniqueConstraint(fields=['project', 'commit_hash'], name='unique_commit_hash_in_project'),
        ]
        ordering = ('-time',)

    def __str__(self):
        return f"[{self.change_list_id}] {self.project.name} {self.time}"

    def save(self, *args, **kwargs):
        ChangeList.validate_unique_fields(
            old_instance=ChangeList.objects.get(pk=self.pk) if self.pk else None,
            new_project=self.project,
            new_change_list_id=self.change_list_id,
            new_commit_hash=self.commit_hash,
        )
        super().save(*args, **kwargs)

    @staticmethod
    def validate_unique_fields(old_instance, new_project, new_change_list_id, new_commit_hash, validation_error_class=ValidationError):
        is_update_operation = bool(old_instance)

        # Check "unique_change_list_id_in_project" constraint
        change_list_id_in_project_uniqueness_error = {"change_list_id": 'This id already exists in this project.'}
        if ChangeList.objects.filter(project=new_project, change_list_id=new_change_list_id).exists():
            if not is_update_operation:
                raise validation_error_class(change_list_id_in_project_uniqueness_error)

            if not (old_instance.project == new_project and old_instance.change_list_id == new_change_list_id):
                raise validation_error_class(change_list_id_in_project_uniqueness_error)

        # Check "unique_commit_hash_in_project" constraint
        commit_hash_in_project_uniqueness_error = {"commit_hash": 'This commit hash already exists in this project.'}
        if ChangeList.objects.filter(project=new_project, commit_hash=new_commit_hash).exists():
            if not is_update_operation:
                raise validation_error_class(commit_hash_in_project_uniqueness_error)

            if not (old_instance.project == new_project and old_instance.commit_hash == new_commit_hash):
                raise validation_error_class(commit_hash_in_project_uniqueness_error)


class Deployment(ExportModelOperationsMixin('Deployment'), SealableModel):
    STATUS_MAX_LENGTH = 1
    STATUS_PASS = 'P'
    STATUS_FAIL = 'F'
    STATUS_CHOICES = (
        (STATUS_PASS, 'pass'),
        (STATUS_FAIL, 'fail'),
    )

    VALIDATION_ERROR_NOT_SAME_PROJECT_IN_CHANGE_LIST_AND_ENVIRONMENT = \
        "Change list does not belong to the same project as the environment."

    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    change_list = models.ForeignKey(ChangeList, on_delete=models.CASCADE)
    status = models.CharField(max_length=STATUS_MAX_LENGTH, choices=STATUS_CHOICES)
    time = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        ordering = ('-time',)

    def __str__(self):
        return "[%s] %s" % (self.pk, self.status)

    # Override
    def save(self, *args, **kwargs):
        if self.environment.project != self.change_list.project:
            raise ValidationError(self.VALIDATION_ERROR_NOT_SAME_PROJECT_IN_CHANGE_LIST_AND_ENVIRONMENT)
        super().save(*args, **kwargs)


class ServiceStatusReport(ExportModelOperationsMixin('ServiceStatusReport'), SealableModel):
    STATUS_MAX_LENGTH = 1
    STATUS_UP = 'U'
    STATUS_DOWN = 'D'
    STATUS_CHOICES = (
        (STATUS_UP, 'up'),
        (STATUS_DOWN, 'down'),
    )

    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    status = models.CharField(max_length=STATUS_MAX_LENGTH, choices=STATUS_CHOICES)
    time = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        ordering = ('-time',)

    def __str__(self):
        return "%s" % self.status
