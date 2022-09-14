from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_prometheus.models import ExportModelOperationsMixin
from seal.models import SealableModel
from apps.dashboard.models.maturity_model import MaturityModelItem
from apps.dashboard.models.project import Project
from apps.utils.formatter import get_readable_time_from_seconds, get_percentage_from_float


class EvaluationRequest(ExportModelOperationsMixin('EvaluationRequest'), SealableModel):
    DESCRIPTION_MAX_LENGTH = 2000
    STATUS_PENDING = 'P'
    STATUS_DONE = 'D'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_DONE, 'Done'),
    )

    maturity_model_item = models.ForeignKey(
        MaturityModelItem,
        on_delete=models.CASCADE,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    time = models.DateTimeField(
        default=timezone.now,
        blank=True,
    )
    description = models.CharField(
        max_length=DESCRIPTION_MAX_LENGTH,
        blank=False,
        null=False,
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    closing_report = models.ForeignKey(
        'EvaluationReport',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"[{self.id}] {self.project.name} {self.maturity_model_item.name} " \
               f"{self.time} {self.applicant} {self.status}"

    @staticmethod
    def get_latest_pending(item: MaturityModelItem, project: Project) -> Optional["EvaluationRequest"]:
        try:
            return EvaluationRequest.objects \
                .filter(maturity_model_item=item) \
                .filter(project=project) \
                .filter(status=EvaluationRequest.STATUS_PENDING) \
                .get()
        except EvaluationRequest.DoesNotExist:
            return None


class EvaluationReport(ExportModelOperationsMixin('EvaluationReport'), SealableModel):
    DESCRIPTION_MAX_LENGTH = 2000
    STATUS_PASS = 'P'
    STATUS_FAIL = 'F'
    STATUS_CHOICES = (
        (STATUS_PASS, 'Pass'),
        (STATUS_FAIL, 'Fail'),
    )
    EVALUATION_VALUE_MAX_LENGTH = 100

    maturity_model_item = models.ForeignKey(
        MaturityModelItem,
        on_delete=models.CASCADE,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
    )
    creation_time = models.DateTimeField(auto_now_add=True)
    last_update_time = models.DateTimeField(auto_now=True)
    latest_evaluation_time = models.DateTimeField(auto_now_add=True)
    description = models.CharField(
        max_length=DESCRIPTION_MAX_LENGTH,
        blank=True,
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    expected_value = models.CharField(
        max_length=EVALUATION_VALUE_MAX_LENGTH,
        blank=True,
        null=True
    )
    current_value = models.CharField(
        max_length=EVALUATION_VALUE_MAX_LENGTH,
        blank=True,
        null=True
    )
    value_type = models.CharField(
        max_length=MaturityModelItem.VALUE_TYPE_MAX_LENGTH,
        choices=MaturityModelItem.ACCEPTABLE_VALUE_TYPE_CHOICES,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = [
            '-last_update_time',
            '-creation_time',
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(latest_evaluation_time__gte=models.F("creation_time")),
                name="evaluation_report_latest_evaluation_time_gte_creation_time",
            ),
            models.CheckConstraint(
                check=models.Q(last_update_time__gte=models.F("creation_time")),
                name="evaluation_report_last_update_time_gte_creation_time",
            ),
        ]

    @staticmethod
    def is_in_validity_period(evaluation_report: EvaluationReport, maturity_model_item: MaturityModelItem, current_time: datetime):
        valid_period_start = evaluation_report.creation_time
        valid_period_end = evaluation_report.latest_evaluation_time + timedelta(days=maturity_model_item.evaluation_type.validity_period_days)
        return valid_period_start <= current_time <= valid_period_end

    def logically_equals(self, other_evaluation_report):
        return (
            self.status == other_evaluation_report.status
            and self.description == other_evaluation_report.description
            and str(self.current_value) == str(other_evaluation_report.current_value)
            and str(self.expected_value) == str(other_evaluation_report.expected_value)
        )

    @classmethod
    def create_new(cls, maturity_model_item: MaturityModelItem, **kwargs):
        if maturity_model_item:
            kwargs.setdefault('value_type', maturity_model_item.acceptable_value_type)
            kwargs.setdefault('expected_value', maturity_model_item.acceptable_value)
        return cls(maturity_model_item=maturity_model_item, **kwargs)

    def __str__(self):
        return f"{self.project.name} " \
               f"{self.maturity_model_item.name} " \
               f"{self.status}"

    @staticmethod
    def get_latest(project, maturity_model_item, before_specific_date=None):
        queryset = EvaluationReport.objects \
            .filter(project=project) \
            .filter(maturity_model_item=maturity_model_item)
        if before_specific_date is not None:
            queryset = queryset.filter(creation_time__date__lte=before_specific_date)
        return queryset.order_by('creation_time').last()

    @property
    def readable_expected_value(self):
        return self.__get_readable_value(self.expected_value)

    @property
    def readable_current_value(self):
        return self.__get_readable_value(self.current_value)

    def __get_readable_value(self, value):
        if self.value_type == MaturityModelItem.VALUE_TYPE_PERCENTAGE:
            try:
                readable_value = get_percentage_from_float(float(value))
            except ValueError:
                readable_value = value
        elif self.value_type == MaturityModelItem.VALUE_TYPE_SECONDS:
            try:
                readable_value = get_readable_time_from_seconds(int(value))
            except ValueError:
                readable_value = value
        else:
            readable_value = value

        return readable_value

    def save(self, force_update_latest_evaluation_time: bool = False, *args, **kwargs):
        if not force_update_latest_evaluation_time:
            latest_evaluation_report = EvaluationReport.get_latest(self.project, self.maturity_model_item)
            is_update_operation_on_latest_evaluation_time = self.pk and EvaluationReport.objects.get(pk=self.pk).latest_evaluation_time != self.latest_evaluation_time
            if (
                is_update_operation_on_latest_evaluation_time
                and latest_evaluation_report is not None
                and latest_evaluation_report.pk != self.pk
            ):
                raise ValueError("Only re-evaluation time of latest evaluation report can be updated.")

        return super().save(*args, **kwargs)


@receiver(post_save, sender=EvaluationReport)
def change_evaluation_requests_status_to_done_after_evaluation_report_submission(instance, **kwargs):
    EvaluationRequest.objects \
        .filter(project=instance.project) \
        .filter(maturity_model_item=instance.maturity_model_item) \
        .filter(status=EvaluationRequest.STATUS_PENDING) \
        .filter(time__lte=instance.creation_time) \
        .update(
            closing_report=instance,
            status=EvaluationRequest.STATUS_DONE,
        )
