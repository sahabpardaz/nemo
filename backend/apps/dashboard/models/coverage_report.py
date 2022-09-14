from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin
from seal.models import SealableModel
from apps.dashboard.models import Project
from apps.utils import validation_utils


class CoverageReport(ExportModelOperationsMixin('CoverageReport'), SealableModel):
    DUPLICATE_COVERAGE_REPORT_ERROR_CODE = 'duplicate-coverage-report'
    TYPE_OVERALL = 'OVR'
    TYPE_INCREMENTAL = 'INC'
    COVERAGE_TYPE_MAX_LENGTH = 3

    project = models.ForeignKey(
        Project,
        related_name='coverage_reports',
        on_delete=models.CASCADE
    )
    value = models.FloatField(
        blank=False,
        null=False,
        validators=[validation_utils.validate_percentage]
    )
    coverage_type = models.CharField(
        max_length=COVERAGE_TYPE_MAX_LENGTH,
        choices=[
            (TYPE_OVERALL, 'Overall Coverage'),
            (TYPE_INCREMENTAL, 'Incremental Coverage (on new code)')
        ],
        null=False,
        blank=False
    )
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
    version = models.TextField(
        null=False,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'coverage_type', 'version'],
                condition=~Q(version__exact=''),
                name='unique_project_and_coverage_type_and_version'
            ),
        ]
        ordering = (
            '-last_update_time',
            '-creation_time',
        )

    @staticmethod
    def validate_version_and_coverage_type_uniqueness_in_project(old_instance, new_project, new_coverage_type, new_version, validation_error_class=ValidationError):
        """
            Check "unique_project_and_coverage_type_and_version" constraint for both update and create operations
        """
        if not new_version:
            # This constraint only applies on non-empty versions
            return

        validation_error = validation_error_class(
            {'version': f'CoverageReport with type {new_coverage_type} and version {new_version} already reported.'},
            code=CoverageReport.DUPLICATE_COVERAGE_REPORT_ERROR_CODE,
        )
        is_update_operation = bool(old_instance)
        coverage_of_this_version_saved_already = CoverageReport.objects.filter(
            project=new_project,
            coverage_type=new_coverage_type,
            version=new_version,
        ).exists()
        if coverage_of_this_version_saved_already:
            if not is_update_operation:
                raise validation_error

            if not (
                old_instance.project == new_project and
                old_instance.coverage_type == new_coverage_type and
                old_instance.version == new_version
            ):
                raise validation_error

    def save(self, *args, **kwargs):
        CoverageReport.validate_version_and_coverage_type_uniqueness_in_project(
            old_instance=CoverageReport.objects.get(pk=self.pk) if self.pk else None,
            new_project=self.project,
            new_coverage_type=self.coverage_type,
            new_version=self.version,
        )
        super().save(*args, **kwargs)

    @staticmethod
    def get_latest(project_id, coverage_type, before_specific_date=None):
        queryset = CoverageReport.objects \
            .filter(project_id=project_id) \
            .filter(coverage_type=coverage_type)
        if before_specific_date is not None:
            queryset = queryset.filter(
                creation_time__date__lte=before_specific_date)
        return queryset.order_by('creation_time').last()

    @staticmethod
    def compute_overall_coverage(project_id, gte_specific_date=None):
        from apps.dashboard.metrics.coverage.computation import OverallCoverageComputer
        from apps.utils.general_utils import convert_date_to_datetime
        # Wrapping up the code mess in the callers:
        project = project_id if isinstance(project_id, Project) else Project.objects.get(id=project_id)
        now = timezone.now()
        checking_period = None if gte_specific_date is None else (now - convert_date_to_datetime(gte_specific_date))
        return OverallCoverageComputer(project, checking_period).compute_for_single_timestamp(now)

    @staticmethod
    def compute_incremental_coverage(project_id, gte_specific_date=None):
        from apps.dashboard.metrics.coverage.computation import IncrementalCoverageComputer
        from apps.utils.general_utils import convert_date_to_datetime
        # Wrapping up the code mess in the callers:
        project = project_id if isinstance(project_id, Project) else Project.objects.get(id=project_id)
        now = timezone.now()
        checking_period = None if gte_specific_date is None else (now - convert_date_to_datetime(gte_specific_date))
        return IncrementalCoverageComputer(project, checking_period).compute_for_single_timestamp(now)
