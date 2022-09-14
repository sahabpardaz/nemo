from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.dashboard.models.project import Project
from apps.dashboard.models.maturity_model import MaturityModelItem
from apps.dashboard.models.evaluation import EvaluationReport


class Goal(models.Model):
    STATUS_NOT_ACHIEVED = 'Not Achieved'
    STATUS_ACHIEVED = 'Achieved'
    STATUS_ON_THE_ROAD = 'On The Road'

    project = models.ForeignKey(
        Project,
        related_name="goals",
        on_delete=models.CASCADE,
    )
    maturity_model_items = models.ManyToManyField(MaturityModelItem)
    due_date = models.DateField()
    creation_time = models.DateTimeField(
        default=timezone.now,
        blank=True,
    )
    last_update_time = models.DateTimeField(
        auto_now=True,
        blank=True,
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ('due_date',)

    @property
    def status(self):
        if self.due_date is None or timezone.now().date() < self.due_date:
            return self.STATUS_ON_THE_ROAD
        else:
            if self.passed_maturity_model_items_count == self.maturity_model_items.count():
                return self.STATUS_ACHIEVED
            else:
                return self.STATUS_NOT_ACHIEVED

    @property
    def passed_maturity_model_items_count(self):
        latest_evaluation_reports = self.get_latest_evaluation_reports_before_due_date()
        passed_maturity_model_items_count = 0
        for evaluation_report in latest_evaluation_reports:
            if evaluation_report.status == EvaluationReport.STATUS_PASS:
                passed_maturity_model_items_count += 1
        return passed_maturity_model_items_count

    def get_latest_evaluation_reports_before_due_date(self):
        evaluation_reports = []
        for maturity_model_item in self.maturity_model_items.all():
            latest_evaluation_report_of_item = EvaluationReport.get_latest(
                project=self.project,
                maturity_model_item=maturity_model_item,
                before_specific_date=self.due_date
            )
            if latest_evaluation_report_of_item:
                evaluation_reports.append(latest_evaluation_report_of_item)

        return evaluation_reports

    def __str__(self):
        return f"{self.project.name} {self.due_date}"

    @classmethod
    def get_closest_goal_based_on_time_for_project_item(cls, project, maturity_model_item):
        return cls.objects \
            .filter(project=project) \
            .filter(maturity_model_items__in=[maturity_model_item]) \
            .first()


@receiver(post_save, sender=Goal)
def create_permissions_for_instance(instance, created, **kwargs):
    if created:
        from apps.dashboard.groups_and_permissions_handler import assign_permissions_to_groups_after_goal_created
        assign_permissions_to_groups_after_goal_created(instance)
