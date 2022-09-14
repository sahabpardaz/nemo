from datetime import datetime
from typing import Optional
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from seal.models import SealableModel
from ordered_model.models import OrderedModel


class MaturityModel(models.Model):
    DESCRIPTION_MAX_LENGTH = 2000

    name = models.CharField(
        unique=True,
        max_length=500,
    )
    description = models.CharField(
        max_length=DESCRIPTION_MAX_LENGTH,
        blank=True,
    )

    def __str__(self):
        return self.name


class MaturityModelLevel(OrderedModel):
    DESCRIPTION_MAX_LENGTH = 2000

    maturity_model = models.ForeignKey(
        MaturityModel,
        on_delete=models.PROTECT,
        related_name='levels',
    )
    order_with_respect_to = 'maturity_model'
    name = models.CharField(max_length=500)
    description = models.CharField(
        max_length=DESCRIPTION_MAX_LENGTH,
        blank=True,
    )

    class Meta(OrderedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                name='dashboard_maturitymodellevel_uk_maturity_model_and_name',
                fields=['maturity_model', 'name'],
            ),
        ]

    def __str__(self):
        maturity_model_str = self.maturity_model.name if hasattr(
            self, 'maturity_model') and self.maturity_model else None
        return f"{maturity_model_str} : {self.name}"


class EvaluationType(models.Model):
    KIND_MANUAL = 'MA'
    KIND_LEAD_TIME = 'LT'
    KIND_DEPLOYMENT_FREQUENCY = 'DF'
    KIND_TIME_TO_RESTORE = 'TR'
    KIND_CHANGE_FAILURE_RATE = 'CF'
    KIND_TEST_COVERAGE = 'TC'
    KIND_INCREMENTAL_TEST_COVERAGE = 'ITC'
    KIND_IS_TEST_COVERAGE_CALCULATED = 'ITCC'
    KIND_DORY = 'DORY'
    KIND_CHOICES = [
        (KIND_MANUAL, 'Manual'),
        ('Devops Metrics', (
            (KIND_LEAD_TIME, 'Lead time'),
            (KIND_DEPLOYMENT_FREQUENCY, 'Deployment frequency'),
            (KIND_TIME_TO_RESTORE, 'Time to restore'),
            (KIND_CHANGE_FAILURE_RATE, 'Change failure rate'),
        )),
        ('Sonar Qube', (
            (KIND_TEST_COVERAGE, 'Commit stage test coverage'),
            (KIND_INCREMENTAL_TEST_COVERAGE,
             'Commit stage incremental test coverage (on new code)'),
        )),
        ('General', (
            (KIND_IS_TEST_COVERAGE_CALCULATED, 'Is test coverage calculated'),
            (KIND_DORY, 'Delegate the evaluation to the project ".nemo.yml" specification.'),
        )),
    ]
    KIND_MAX_LENGTH = 5

    kind = models.CharField(
        max_length=KIND_MAX_LENGTH,
        choices=KIND_CHOICES,
    )
    validity_period_days = models.IntegerField(
        blank=True,
        null=True,
        default=0,
        help_text="In days",
    )
    checking_period_days = models.IntegerField(
        blank=True,
        null=True,
        default=0,
        help_text="In days",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='dashboard_maturitymodelitem_uk_non_manual_kind',
                fields=['kind'],
                condition=~Q(kind='MA'),
            )
        ]

    def __str__(self):
        return f"[{self.get_kind_display()}] Checking:{self.checking_period_days}, Validity:{self.validity_period_days}"

    def save(self, *args, **kwargs):
        EvaluationType.validate_kind_uniqueness(self.kind, self.pk)
        super().save(*args, **kwargs)

    @staticmethod
    def _raise_duplicate_kind_error(kind):
        raise ValidationError(f"There is already exists an evaluation type with kind {kind}")

    @staticmethod
    def validate_kind_uniqueness(new_instance_kind, old_instance_pk):
        if (
            new_instance_kind != EvaluationType.KIND_MANUAL
            and EvaluationType.objects.filter(kind=new_instance_kind).exists()
        ):
            if not old_instance_pk:
                EvaluationType._raise_duplicate_kind_error(new_instance_kind)

            old_evaluation_type = EvaluationType.objects.get(pk=old_instance_pk)
            if new_instance_kind != old_evaluation_type.kind:
                EvaluationType._raise_duplicate_kind_error(new_instance_kind)


class MaturityModelItem(OrderedModel):
    DESCRIPTION_MAX_LENGTH = 2000
    VALUE_TYPE_SECONDS = 'SEC'
    VALUE_TYPE_PERCENTAGE = 'PRC'
    ACCEPTABLE_VALUE_TYPE_CHOICES = (
        (VALUE_TYPE_SECONDS, 'Seconds'),
        (VALUE_TYPE_PERCENTAGE, 'Percentage'),
    )
    VALUE_TYPE_MAX_LENGTH = 5

    maturity_model_level = models.ForeignKey(
        MaturityModelLevel,
        on_delete=models.PROTECT,
        related_name='items',
    )
    #Invariant: item.maturity_model = item.maturity_model_level.maturity_model
    maturity_model = models.ForeignKey(
        MaturityModel,
        on_delete=models.PROTECT,
        related_name='items',
    )
    order_with_respect_to = 'maturity_model_level'
    code = models.CharField(max_length=4)
    name = models.CharField(max_length=500)
    description = models.CharField(
        max_length=DESCRIPTION_MAX_LENGTH,
        blank=True,
    )
    acceptable_value = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )
    acceptable_value_type = models.CharField(
        max_length=VALUE_TYPE_MAX_LENGTH,
        choices=ACCEPTABLE_VALUE_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    evaluation_type = models.ForeignKey(
        EvaluationType,
        on_delete=models.PROTECT,
        related_name='items',
    )

    class Meta(OrderedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                name='dashboard_maturitymodelitem_uk_maturity_model_level_and_name',
                fields=['maturity_model_level', 'name'],
            ),
            models.UniqueConstraint(
                name='dashboard_maturitymodelitem_uk_maturity_model_and_code',
                fields=['maturity_model', 'code'],
            ),
        ]

    def save(self, *args, **kwargs):
        self.maturity_model = self.maturity_model_level.maturity_model
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.maturity_model_level.maturity_model.name} :" \
               f" {self.maturity_model_level.name} => {self.name}"

    def is_disabled(self, project, timestamp: datetime = None) -> bool:
        """
        Returns True if the item is disabled currently or at the given timestamp.
        """
        latest_approved_toggle_requests = self.toggle_requests \
            .filter(project=project) \
            .filter(approval__approved=True) \
            .only('disable') \
            .seal() \
            .order_by('creation_time')
        if timestamp is not None:
            latest_approved_toggle_requests = latest_approved_toggle_requests.filter(creation_time__lte=timestamp)
        latest_approved_toggle_request = latest_approved_toggle_requests.last()
        if latest_approved_toggle_request is None:
            return False
        return latest_approved_toggle_request.disable

    def has_pending_toggle_request(self, project, request_for_disable: bool = None):
        """
        Returns true if item has pending request.
        You can specify `request_for_disable` if you want
        to check that pending request exists for disabling/enabling item.
        """
        latest_pending_request = self._get_latest_pending_toggle_request(project)
        if latest_pending_request is None:
            return False

        if request_for_disable is None:
            return True

        return latest_pending_request.disable == request_for_disable

    def _get_latest_pending_toggle_request(self, project):
        return self.toggle_requests \
            .filter(project=project) \
            .filter(approval__isnull=True) \
            .order_by('creation_time') \
            .last()


@receiver(post_save, sender=MaturityModelLevel)
def update_model_in_items(instance, **kwargs):
    instance.items.update(maturity_model=instance.maturity_model)


class MaturityModelItemToggleRequest(SealableModel):
    REASON_MAX_LENGTH = 2000

    disable = models.BooleanField()
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
    )
    maturity_model_item = models.ForeignKey(
        MaturityModelItem,
        on_delete=models.CASCADE,
        related_name="toggle_requests",
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    reason = models.CharField(
        max_length=REASON_MAX_LENGTH,
        blank=False,
        null=False,
    )
    creation_time = models.DateTimeField(auto_now_add=True)

    @property
    def action_type(self):
        return 'disable' if self.disable else 'enable'

    def __str__(self):
        return f"{self.action_type} {self.maturity_model_item} for {self.project}"

    @staticmethod
    def get_latest_pending(item: MaturityModelItem, project) -> Optional["MaturityModelItemToggleRequest"]:
        try:
            return MaturityModelItemToggleRequest.objects \
                .filter(maturity_model_item=item) \
                .filter(project=project) \
                .filter(approval__isnull=True) \
                .get()
        except MaturityModelItemToggleRequest.DoesNotExist:
            return None


class MaturityModelItemToggleApproval(models.Model):
    REASON_MAX_LENGTH = 2000

    maturity_model_item_toggle_request = models.OneToOneField(
        MaturityModelItemToggleRequest,
        on_delete=models.CASCADE,
        related_name="approval",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    reason = models.CharField(
        max_length=REASON_MAX_LENGTH,
        blank=True,
    )
    approved = models.BooleanField(default=False)
    creation_time = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=MaturityModelItemToggleApproval)
def close_related_evaluation_requests(instance, created, **kwargs):
    from apps.dashboard.models import EvaluationRequest, EvaluationReport

    item_toggle_request = instance.maturity_model_item_toggle_request

    if not created:
        return

    if not instance.approved:
        return

    EvaluationReport.create_new(
        maturity_model_item=item_toggle_request.maturity_model_item,
        project=item_toggle_request.project,
        status=EvaluationReport.STATUS_FAIL,
        description="This Item disabled for this project.",
        current_value="Disabled",
    ).save()
