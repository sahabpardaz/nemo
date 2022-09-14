import os
import json
import dataclasses
from datetime import timedelta, datetime
from typing import Optional, List
from dataclasses import dataclass
from uuid import uuid4
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone
from django.db.models import Q
from apps.dashboard.models.project import Project


@dataclass
class MaturityItemDoryResult:
    code: str
    passed: bool
    description: str


def get_maturity_item_dory_results_file_path(instance, filename):
    if instance.pk is not None:
        name = f"report-{instance.pk}.json"
    else:
        name = f"report-U{uuid4().hex}.json"
    return os.path.join(settings.DORY_EVALUATION_RESULTS_SUBDIR, name)


class DoryEvaluation(models.Model):
    MAX_LENGTH_SUBMISSION_ID = 36
    DORY_POLLING_TIMEOUT_SECONDS = 2 * 24 * 60 * 60

    project = models.ForeignKey(
        Project,
        related_name="dory_evaluations",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    submission_time = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=False,
    )
    first_completed_poll_time = models.DateTimeField(
        # first_completed_poll_time is evaluation_completed_time +- (AUTO_DATA_COLLECTION_INTERVAL)
        blank=True,
        null=True,
    )
    submission_id = models.CharField(
        max_length=MAX_LENGTH_SUBMISSION_ID,
        blank=False,
        null=False,
    )
    maturity_item_dory_results_file = models.FileField(
        null=False,
        blank=True,
        upload_to=get_maturity_item_dory_results_file_path,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(first_completed_poll_time__gte=models.F("submission_time")),
                name="first_completed_poll_time_gte_submission_time",
            ),
        ]

    def set_maturity_item_dory_results(self, maturity_item_dory_results: List[MaturityItemDoryResult]):
        self.maturity_item_dory_results_file.save(
            name="",
            content=ContentFile(content=json.dumps([dataclasses.asdict(i) for i in maturity_item_dory_results])),
            save=False,
        )

    def get_maturity_item_dory_result(self, item_code: str) -> Optional[MaturityItemDoryResult]:
        """Opens 'maturity_item_dory_results_file' and returns specified item result."""
        if not self.maturity_item_dory_results_file:
            return

        with self.maturity_item_dory_results_file.open('r') as results_file:
            maturity_item_dory_results = json.loads(results_file.read())

        maturity_item_dory_result = next((ir for ir in maturity_item_dory_results if ir['code'] == item_code), None)
        if maturity_item_dory_result is None:
            return None
        return MaturityItemDoryResult(**maturity_item_dory_result)

    @staticmethod
    def get_latest_non_completed_evaluation(project: Project):
        dory_evaluation = (project.dory_evaluations
            .order_by('submission_time')
            .filter(
                Q(first_completed_poll_time__isnull=True)
                | Q(first_completed_poll_time__gte=timezone.now() - timedelta(minutes=settings.AUTO_EVALUATION_INTERVAL_IN_MINUTES))
            )
            .filter(submission_time__gt=timezone.now() - timedelta(seconds=DoryEvaluation.DORY_POLLING_TIMEOUT_SECONDS))
            .last()
        )
        return dory_evaluation

    @staticmethod
    def get_completed_evaluations_in_checking_period(project: Project, checking_period_days: int, current_time: datetime) -> QuerySet:
        checking_period_start = current_time - timedelta(days=checking_period_days)
        checking_period_end = current_time
        return (DoryEvaluation.objects
            .filter(project=project)
            .filter(first_completed_poll_time__isnull=False)
            .filter(submission_time__gte=checking_period_start)
            .filter(first_completed_poll_time__lt=checking_period_end)
            .order_by('submission_time')
        )
