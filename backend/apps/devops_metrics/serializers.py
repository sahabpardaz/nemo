from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.dashboard.models import Project, Environment
from apps.devops_metrics.constants import (
    ENVIRONMENT_ID_URL_PARAMETER,
    DEFAULT_CHECKING_PERIOD_DAYS,
    DEFAULT_PERIOD_IN_DAYS,
    MAX_PERIOD_IN_DAYS,
)
from apps.devops_metrics.models import ChangeList, \
    Deployment, ServiceStatusReport
from apps.utils import exception_utils
from apps.utils.validation_utils import InconsistentDataError, SerializerValidateAndSaveMixin


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']
        ref_name = 'devopsmetrics_project'


class ChangeListSerializer(serializers.ModelSerializer, SerializerValidateAndSaveMixin):
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ChangeList
        fields = ['id', 'project', 'change_list_id', 'commit_hash', 'time', 'title']
        extra_kwargs = {'parent_lookup_project_id': {'required': True}}

    def create(self, validated_data):
        validated_data["project"] = Project.objects.get(
            pk=self.context.get("project_id")
        )
        return super().create(validated_data)

    def validate(self, attrs):
        project = Project.objects.get(
            pk=self.context.get("project_id")
        )
        change_list_id = attrs.get('change_list_id')
        commit_hash = attrs.get('commit_hash')

        ChangeList.validate_unique_fields(
            old_instance=self.instance if self.instance else None,
            new_project=project,
            new_change_list_id=change_list_id,
            new_commit_hash=commit_hash,
            validation_error_class=serializers.ValidationError,
        )
        return attrs

    @classmethod
    def _handle_save_error(cls, e: Exception, instance=None, data=..., **kwargs):
        if exception_utils.is_exception_about_unique_constraint(e):
            if instance is None:
                commit_hash = data.get('commit_hash')
                change_list_id = data.get('change_list_id')
            else:
                commit_hash = instance.commit_hash
                change_list_id = instance.change_list_id
            info_already_exist_in_a_single_cl = ChangeList.objects.filter(commit_hash=commit_hash, change_list_id=change_list_id).exists()
            if not info_already_exist_in_a_single_cl:
                raise InconsistentDataError(f"Couldn't save a changelist with commit_hash={commit_hash} and change_list_id={change_list_id} "
                                            "because of a unique constraint violation. But this tuple of info doesn't exist in a single record at DB. "
                                            "Perhaps a data inconsistency has been occured; e.g. a CL is saved (or trying to save) with commit hash of another.")
        raise e


class DeploymentSerializer(serializers.ModelSerializer):
    environment = serializers.PrimaryKeyRelatedField(read_only=True)
    commit_hash = serializers.CharField(write_only=True)
    change_list = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Deployment
        fields = ['id', 'environment', 'change_list', 'status', 'time', 'commit_hash']

    def create(self, validated_data):
        validated_data["environment"] = Environment.objects.get(pk=self.context["view"]
                                                                .kwargs[ENVIRONMENT_ID_URL_PARAMETER])
        validated_data["change_list"] = ChangeList.objects.get(project=validated_data.get("environment").project,
                                                               commit_hash=validated_data.get("commit_hash"))

        return Deployment.objects.create(environment=validated_data.get("environment"),
                                         change_list=validated_data.get("change_list"),
                                         status=validated_data.get("status"))

    def validate(self, attrs):
        commit_hash = attrs.get("commit_hash")
        environment = Environment.objects.get(pk=self.context["view"]
                                              .kwargs[ENVIRONMENT_ID_URL_PARAMETER])
        try:
            change_list = ChangeList.objects.get(project=environment.project, commit_hash=commit_hash)
        except ChangeList.DoesNotExist:
            raise serializers.ValidationError("Changelist with this commit hash not found for this project.")

        if 'time' in attrs and attrs.get('time') < change_list.time:
            raise serializers.ValidationError("Deployment is before Changelist time!")

        attrs['change_list'] = change_list

        return attrs


class ServiceStatusReportSerializer(serializers.ModelSerializer):
    environment = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ServiceStatusReport
        fields = ['id', 'environment', 'status', 'time']

    def create(self, validated_data):
        validated_data["environment"] = Environment.objects.get(pk=self.context["view"]
                                                                .kwargs[ENVIRONMENT_ID_URL_PARAMETER])
        return ServiceStatusReport.objects.create(**validated_data)


class MetricDataPointSerializer(serializers.Serializer):
    date = serializers.SerializerMethodField(method_name='get_data_point_date', read_only=True)
    value = serializers.SerializerMethodField(method_name='get_data_point_value', read_only=True)

    def get_data_point_date(self, obj):
        return obj[0]

    def get_data_point_value(self, obj):
        return obj[1]

    def update(self, instance, validated_data):
        raise NotImplementedError("Metric data points are calculated by 'MetricComputer's and can't be updated.")

    def create(self, validated_data):
        raise NotImplementedError("Metric data points are calculated by 'MetricComputer's and can't be created.")


def get_today_date():
    return timezone.now().date()


class DailyMetricReportRequestParametersSerializer(serializers.Serializer):
    checking_period_days = serializers.IntegerField(
        default=DEFAULT_CHECKING_PERIOD_DAYS,
        min_value=1,
    )
    period_start_date = serializers.DateField(
        default=None,
    )
    period_end_date = serializers.DateField(
        default=get_today_date,
    )

    def validate(self, attrs):
        if attrs.get('period_start_date') is None:
            attrs['period_start_date'] = attrs.get('period_end_date') - timedelta(days=DEFAULT_PERIOD_IN_DAYS)

        if attrs.get('period_start_date') > attrs.get('period_end_date'):
            raise serializers.ValidationError(detail="Period ends before it starts.")

        if attrs.get('period_end_date') - attrs.get('period_start_date') > timedelta(days=MAX_PERIOD_IN_DAYS):
            raise serializers.ValidationError(detail=f"Period should not be greater than {MAX_PERIOD_IN_DAYS} days.")

        if attrs.get('period_end_date') > get_today_date():
            raise serializers.ValidationError(detail="Period end date must not be in the future.")

        return attrs
