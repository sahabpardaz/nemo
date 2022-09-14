import itertools
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.status import HTTP_409_CONFLICT
from apps.dashboard.models import (
    EvaluationRequest,
    Project,
    MaturityModelItem,
    Goal,
    GitlabProject,
    SonarProject,
    MaturityModelLevel,
    MaturityModel,
    Environment,
    EvaluationType,
    MaturityModelItemToggleRequest,
    UserProjectNotifSetting,
    DoryEvaluation,
)
from apps.dashboard.models.coverage_report import CoverageReport
from apps.dashboard.models.evaluation import EvaluationReport
from apps.dashboard.models.project import ProjectAPIToken
from apps.dashboard.models.project_maturity_state import ProjectMaturityItemState, ProjectMaturityState
from apps.devops_metrics.constants import PROJECT_ID_URL_PARAMETER
from apps.utils.general_utils import truncated_to_str
from apps.utils.serializer_utils import (
    set_one_to_many_composition,
    DynamicFieldsModelSerializer,
)
from apps.utils.validation_utils import check_for_duplicate_values_in_unique_fields, SerializerValidateAndSaveMixin


class EvaluationRequestSerializer(serializers.ModelSerializer):
    project = serializers.CharField(read_only=True)
    applicant = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EvaluationRequest
        fields = ['id', 'project', 'maturity_model_item',
                  'time', 'description', 'applicant']
        extra_kwargs = {'parent_lookup_project_id': {'required': True}}

    def validate_maturity_model_item(self, value):
        if value.evaluation_type.kind not in [
            EvaluationType.KIND_MANUAL,
            EvaluationType.KIND_DORY
        ]:
            raise serializers.ValidationError('Evaluation of the given maturity model item is done automatically by Nemo.')
        return value

    def validate(self, attrs):
        is_update_operation = bool(self.instance)
        if is_update_operation:
            return self.validate_on_update(attrs)
        return self.validate_on_create(attrs)

    def validate_on_update(self, attrs):
        evaluation_request_applicant_user = self.instance.applicant
        if evaluation_request_applicant_user != self.context.get("user"):
            raise serializers.ValidationError(
                f'Only user {evaluation_request_applicant_user} can edit this evaluation request.')

        if self.instance.status != EvaluationRequest.STATUS_PENDING:
            raise serializers.ValidationError('Only pending requests can be edited.')

        if (
                attrs.get('maturity_model_item') is not None and
                self.instance.maturity_model_item != attrs.get('maturity_model_item')
        ):
            raise serializers.ValidationError(f'You can not update maturity model item.')

        return attrs

    def validate_on_create(self, attrs):
        project_id = self.context.get("project_id")
        maturity_model_item = attrs.get('maturity_model_item')

        if maturity_model_item.is_disabled(Project.objects.get(id=project_id)):
            raise serializers.ValidationError('This item disabled for this project and cannot be evaluated.')

        any_pending_req_exists = EvaluationRequest.objects.filter(
            project_id=project_id,
            maturity_model_item=maturity_model_item,
            status=EvaluationRequest.STATUS_PENDING
        ).exists()
        if any_pending_req_exists:
            raise serializers.ValidationError('A pending request already exists.', code=HTTP_409_CONFLICT)

        return attrs

    def create(self, validated_data):
        validated_data["project"] = Project.objects.get(id=self.context.get("project_id"))
        validated_data["applicant"] = self.context.get("user")
        return EvaluationRequest.objects.create(**validated_data)

    @staticmethod
    def validate_on_delete(instance: EvaluationRequest):
        if instance.status != EvaluationRequest.STATUS_PENDING:
            raise serializers.ValidationError(f"Only pending request can be deleted.")


class UserPublicInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']


class EnvironmentSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Environment
        fields = ['id', 'project', 'name', 'description']

    def create(self, validated_data):
        validated_data["project"] = Project.objects.get(pk=self.context["view"].kwargs[PROJECT_ID_URL_PARAMETER])
        return Environment.objects.create(**validated_data)


class ProjectSerializer(DynamicFieldsModelSerializer):
    creator = UserPublicInformationSerializer()
    default_environment = EnvironmentSerializer()

    class Meta:
        model = Project
        fields = ['id', 'name', 'maturity_model', 'creator', 'default_environment']
        ref_name = 'dashboard_project'


class GoalSerializer(DynamicFieldsModelSerializer):
    id = serializers.IntegerField(read_only=True)
    creator = serializers.CharField(read_only=True)
    creation_time = serializers.DateTimeField(read_only=True)
    maturity_model_levels_involved = serializers.SerializerMethodField(
        method_name='get_maturity_model_levels_involved'
    )

    class Meta:
        model = Goal
        fields = [
            'id',
            'due_date',
            'creation_time',
            'creator',
            'status',
            'maturity_model_items',
            'maturity_model_levels_involved',
            'passed_maturity_model_items_count',
        ]

    def validate(self, attrs):
        project = Project.objects.get(pk=self.context["view"].kwargs[PROJECT_ID_URL_PARAMETER])
        for maturity_model_item in attrs.get("maturity_model_items"):
            if maturity_model_item.is_disabled(project):
                raise serializers.ValidationError(
                    {'maturity_model_items': f'Item {maturity_model_item.code} disabled for this project.'}
                )

            if maturity_model_item.has_pending_toggle_request(project=project, request_for_disable=True):
                raise serializers.ValidationError(
                    {
                        'maturity_model_items': f'Item {maturity_model_item.code} requested to be disabled for this project.'}
                )

        return attrs

    def validate_due_date(self, value):
        if value <= timezone.now().date():
            raise serializers.ValidationError("Date should not be in the past.")
        return value

    def create(self, validated_data):
        validated_data['project'] = Project.objects.get(
            pk=self.context["view"].kwargs[PROJECT_ID_URL_PARAMETER])
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def get_maturity_model_levels_involved(self, obj):
        levels_involved = set()
        for item in obj.maturity_model_items.all():
            levels_involved.add(item.maturity_model_level.name)
        return list(levels_involved)


class SonarProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SonarProject
        fields = ['project_key', 'api_base_url']


class GitlabProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitlabProject
        fields = ['project_id', 'default_branch']


class EvaluationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationType
        fields = [
            'kind',
            'validity_period_days',
            'checking_period_days',
        ]


class MaturityModelItemPreviewSerializer(serializers.ModelSerializer):
    evaluation_type = serializers.SerializerMethodField()

    class Meta:
        model = MaturityModelItem
        fields = [
            'id', 'code', 'name', 'evaluation_type',
        ]

    def create(self, validated_data):
        raise NotImplementedError("This is a light readonly serializer.")

    def get_evaluation_type(self, obj: MaturityModelItem):
        return {
            'kind': obj.evaluation_type.kind
        }


class MaturityModelItemSerializer(serializers.ModelSerializer):
    evaluation_type = EvaluationTypeSerializer()

    class Meta:
        model = MaturityModelItem
        fields = [
            'id', 'code', 'name', 'description', 'evaluation_type',
            'acceptable_value', 'acceptable_value_type',
        ]

    # Override
    def validate(self, attrs):
        maturity_model_level = attrs.get('maturity_model_level', None)
        # This kind of check is only useful when the parent is also set and already saved in DB.
        # It does not check the uniqueness among unsaved siblings.
        if maturity_model_level:
            name = attrs['name']
            if MaturityModelItem.objects.filter(maturity_model_level=maturity_model_level, name=name).exists():
                raise serializers.ValidationError('A maturity model item with this name already exists in this level.')
            maturity_model = maturity_model_level.maturity_model
            if maturity_model:
                code = attrs['code']
                if MaturityModelItem.objects.filter(maturity_model=maturity_model, code=code).exists():
                    raise serializers.ValidationError(
                        'A maturity model item with this code already exists in this model.')
        return attrs

    def create(self, validated_data):
        evaluation_type_data = validated_data['evaluation_type']
        if evaluation_type_data is None:
            raise serializers.ValidationError('Maturity model item should have evaluation type.')

        if evaluation_type_data['kind'] == EvaluationType.KIND_MANUAL:
            validated_data['evaluation_type'] = EvaluationType.objects.create(**evaluation_type_data)
        else:
            validated_data['evaluation_type'] = EvaluationType.objects.get_or_create(**evaluation_type_data)[0]

        return MaturityModelItem.objects.create(**validated_data)


class MaturityModelLevelSerializer(serializers.ModelSerializer):
    items = MaturityModelItemSerializer(many=True)

    class Meta:
        model = MaturityModelLevel
        fields = ['name', 'description', 'items', ]

    # Override
    def validate(self, attrs):
        maturity_model = attrs.get('maturity_model', None)
        # This kind of check is only useful when the parent is also set and already saved in DB.
        # It does not check the uniqueness among unsaved siblings.
        if maturity_model:
            name = attrs['name']
            if MaturityModelLevel.objects.filter(maturity_model=maturity_model, name=name).exists():
                raise serializers.ValidationError('A maturity model level with this name already exists in this model.')
        return attrs

    def validate_items(self, value):
        # This check is useful when the data is not persisted yet.
        check_for_duplicate_values_in_unique_fields(value, "name")
        return value

    # Override
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        maturity_model_level = MaturityModelLevel.objects.create(**validated_data)
        set_one_to_many_composition(
            parent_instance=maturity_model_level,
            child_list_data=items_data,
            child_serializer=self.fields['items'],
            parent_name='maturity_model_level',
            children_name='items',
        )
        return maturity_model_level


class MaturityModelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    levels = MaturityModelLevelSerializer(many=True)

    class Meta:
        model = MaturityModel
        fields = ['id', 'name', 'description', 'levels', ]

    def validate_levels(self, value):
        # This check is useful when the data is not persisted yet.
        check_for_duplicate_values_in_unique_fields(value, "name")
        return value

    # Override
    def validate(self, attrs):
        def error_message_builder_for_duplicate_item_codes(keys, duplicate_values) -> str:
            return f"Duplicate values for code in the items of this model: {truncated_to_str(duplicate_values.keys(), 3)}"

        # This check is useful when the data is not persisted yet.
        levels = attrs.get('levels', [])
        all_model_items = itertools.chain.from_iterable(level.get('items', []) for level in levels)
        check_for_duplicate_values_in_unique_fields(
            items=all_model_items,
            keys="code",
            message_builder=error_message_builder_for_duplicate_item_codes
        )
        return attrs

    # Override
    def create(self, validated_data):
        levels_data = validated_data.pop('levels', [])
        maturity_model = MaturityModel.objects.create(**validated_data)
        set_one_to_many_composition(
            parent_instance=maturity_model,
            child_list_data=levels_data,
            child_serializer=self.fields['levels'],
            parent_name='maturity_model',
            children_name='levels',
        )
        return maturity_model


class CoverageReportSerializer(serializers.ModelSerializer, SerializerValidateAndSaveMixin):
    class Meta:
        model = CoverageReport
        fields = ['id', 'value', 'coverage_type', 'creation_time', 'last_update_time', 'version']

    def create(self, validated_data):
        validated_data['project'] = Project.objects.get(pk=self.context.get("project_id"))
        user = self.context.get("user")
        if not isinstance(user, AnonymousUser):
            validated_data["creator"] = user
        return super().create(validated_data)

    def validate(self, attrs):
        coverage_type = attrs.get('coverage_type')
        version = attrs.get('version')
        project = Project.objects.get(pk=self.context.get("project_id"))
        CoverageReport.validate_version_and_coverage_type_uniqueness_in_project(
            old_instance=self.instance if self.instance else None,
            new_project=project,
            new_coverage_type=coverage_type,
            new_version=version,
            validation_error_class=serializers.ValidationError,
        )
        return attrs


class MaturityModelItemToggleRequestSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(read_only=True)
    applicant = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MaturityModelItemToggleRequest
        fields = [
            'disable',
            'project',
            'maturity_model_item',
            'reason',
            'applicant',
            'creation_time',
        ]

    def validate(self, attrs):
        is_update_operation = bool(self.instance)
        if is_update_operation:
            return self.validate_on_update(attrs)
        return self.validate_on_create(attrs)

    def validate_on_create(self, attrs):
        maturity_model_item = attrs.get('maturity_model_item')
        disable = attrs.get('disable')
        project = Project.objects.get(pk=self.context.get("project_id"))

        goals_contain_maturity_model_item = Goal.objects.filter(project=project) \
            .filter(maturity_model_items__id__contains=maturity_model_item.id) \
            .values_list('id', flat=True).order_by('id')
        if goals_contain_maturity_model_item:
            raise serializers.ValidationError(
                f"Can not disable this item since this item exists "
                f"in goals {','.join(map(str, goals_contain_maturity_model_item))}"
            )

        if maturity_model_item.is_disabled(project) and disable:
            raise serializers.ValidationError('This item already disabled for this project.')

        if not maturity_model_item.is_disabled(project) and not disable:
            raise serializers.ValidationError('This item already enabled for this project.')

        if maturity_model_item.has_pending_toggle_request(project):
            raise serializers.ValidationError('A pending request already exists.')

        return attrs

    def validate_on_update(self, attrs):
        evaluation_request_applicant_user = self.instance.applicant
        if evaluation_request_applicant_user != self.context.get("user"):
            raise serializers.ValidationError(
                f'Only user {evaluation_request_applicant_user} can edit this evaluation request.')

        if hasattr(self.instance, 'approval'):
            raise serializers.ValidationError('Only pending requests can be edited.')

        if (
                attrs.get('maturity_model_item') is not None and
                self.instance.maturity_model_item != attrs.get('maturity_model_item')
        ):
            raise serializers.ValidationError(f'You can not update maturity model item.')

        return attrs

    @staticmethod
    def validate_on_delete(instance: MaturityModelItemToggleRequest):
        if hasattr(instance, 'approval'):
            raise serializers.ValidationError(f"Only pending request can be deleted.")

    def create(self, validated_data):
        project = Project.objects.get(pk=self.context.get("project_id"))
        validated_data["project"] = project
        validated_data["applicant"] = self.context.get("user")
        return MaturityModelItemToggleRequest.objects.create(**validated_data)


class UserHyperlinkedReferenceSerializer(serializers.ModelSerializer):
    title = serializers.CharField(read_only=True, source='username')
    admin_page_url = serializers.SerializerMethodField()

    def get_admin_page_url(self, obj: User) -> str:
        # pylint: disable=no-self-use
        return settings.FRONTEND_HOST + reverse('admin:auth_user_change', args=(obj.id,))

    class Meta:
        model = User
        fields = [
            'title',
            'admin_page_url',
        ]


class ProjectHyperlinkedReferenceSerializer(serializers.ModelSerializer):
    title = serializers.CharField(read_only=True, source='name')
    dashboard_page_url = serializers.SerializerMethodField()

    def get_dashboard_page_url(self, obj: Project) -> str:
        # pylint: disable=no-self-use
        return f"{settings.FRONTEND_HOST}/project/{obj.id}/dashboard"

    class Meta:
        model = Project
        fields = [
            'title',
            'dashboard_page_url',
        ]


class EvaluationRequestHyperlinkedReferenceSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    admin_page_url = serializers.SerializerMethodField()

    def get_title(self, obj: EvaluationRequest) -> str:
        # pylint: disable=no-self-use
        return f"Evaluation Request {obj.pk}"

    def get_admin_page_url(self, obj: EvaluationRequest) -> str:
        # pylint: disable=no-self-use
        return settings.FRONTEND_HOST + reverse('admin:dashboard_evaluationrequest_change', args=(obj.id,))

    class Meta:
        model = EvaluationRequest
        fields = [
            'title',
            'admin_page_url',
        ]


# Todo: Refactor ProjectMaturityModelItemRelationshipInEvaluationRequestSerializer,
# ProjectMaturityModelItemRelationshipInToggleRequestSerializer in a better way
class ProjectMaturityModelItemRelationshipSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    dashboard_page_url = serializers.SerializerMethodField()

    def get_title(self, obj) -> str:
        # pylint: disable=no-self-use
        return obj.maturity_model_item.name

    def get_dashboard_page_url(self, obj) -> str:
        # pylint: disable=no-self-use
        return f"{settings.FRONTEND_HOST}/project/{obj.project.id}/maturity-model/item/{obj.maturity_model_item.id}"

    class Meta:
        fields = [
            'title',
            'dashboard_page_url',
        ]


class ProjectMaturityModelItemRelationshipInEvaluationRequestSerializer(ProjectMaturityModelItemRelationshipSerializer):
    class Meta(ProjectMaturityModelItemRelationshipSerializer.Meta):
        model = EvaluationRequest


class ProjectMaturityModelItemRelationshipInToggleRequestSerializer(ProjectMaturityModelItemRelationshipSerializer):
    class Meta(ProjectMaturityModelItemRelationshipSerializer.Meta):
        model = MaturityModelItemToggleRequest


class EvaluationRequestEmailSerializer(serializers.ModelSerializer):
    evaluation_request = EvaluationRequestHyperlinkedReferenceSerializer(source='*')
    project = ProjectHyperlinkedReferenceSerializer()
    maturity_model_item = ProjectMaturityModelItemRelationshipInEvaluationRequestSerializer(source='*')
    applicant = UserHyperlinkedReferenceSerializer()
    status = serializers.CharField(read_only=True, source='get_status_display')
    time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    subject = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()

    def get_action(self, obj):
        return self.context['action']

    def get_subject(self, obj: EvaluationRequest) -> str:
        return f"Evaluation Request Of Item {obj.maturity_model_item.code} for project {obj.project.name} {self.context['action']}"

    class Meta:
        model = EvaluationRequest
        fields = [
            'action',
            'subject',
            'evaluation_request',
            'project',
            'maturity_model_item',
            'time',
            'description',
            'applicant',
            'status',
        ]


class ToggleRequestHyperlinkedReferenceSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    admin_page_url = serializers.SerializerMethodField()

    def get_title(self, obj: MaturityModelItemToggleRequest) -> str:
        return f"Request to {obj.action_type} item {obj.maturity_model_item.code}"

    def get_admin_page_url(self, obj: MaturityModelItemToggleRequest) -> str:
        return settings.FRONTEND_HOST + reverse('admin:dashboard_maturitymodelitemtogglerequest_change', args=(obj.id,))

    class Meta:
        model = EvaluationRequest
        fields = [
            'title',
            'admin_page_url',
        ]


class ToggleRequestEmailSerializer(serializers.ModelSerializer):
    toggle_request = ToggleRequestHyperlinkedReferenceSerializer(source='*')
    project = ProjectHyperlinkedReferenceSerializer()
    maturity_model_item = ProjectMaturityModelItemRelationshipInToggleRequestSerializer(source='*')
    applicant = UserHyperlinkedReferenceSerializer()
    creation_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    subject = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()

    def get_action(self, obj):
        return self.context['action']

    def get_subject(self, obj: MaturityModelItemToggleRequest) -> str:
        return f"Request to {obj.action_type} item {obj.maturity_model_item.code} for {obj.project.name} {self.context['action']}"

    class Meta:
        model = MaturityModelItemToggleRequest
        fields = [
            'action',
            'subject',
            'toggle_request',
            'project',
            'maturity_model_item',
            'creation_time',
            'applicant',
            'reason',
            'disable',
        ]


class ProjectAPITokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAPIToken
        fields = ['key']


class ProjectMaturityStateParametersSerializer(serializers.Serializer):
    snapshot_time = serializers.DateTimeField(
        default=timezone.now,
    )

    def validate_snapshot_time(self, value):
        current_time = timezone.now()
        if value > current_time:
            raise serializers.ValidationError("Project snapshot time must not be in the future.")

        return value


class EvaluationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationReport
        fields = ['id', 'status', 'latest_evaluation_time',
                  'expected_value', 'current_value', 'value_type',
                  'description']


class ProjectMaturityItemStatePreviewSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        raise NotImplementedError("Maturity state is a calculated entity.")

    def create(self, validated_data):
        raise NotImplementedError("Maturity state is a calculated entity.")

    maturity_item = MaturityModelItemPreviewSerializer()
    disabled = serializers.BooleanField(source="is_disabled")
    latest_pending_evaluation_request_id = serializers.IntegerField()
    is_passed = serializers.BooleanField()
    closest_goal = GoalSerializer(fields=('id', 'due_date'))


class ProjectMaturityItemStateSerializer(ProjectMaturityItemStatePreviewSerializer):
    maturity_item = MaturityModelItemSerializer()
    latest_evaluation_report = EvaluationReportSerializer()
    failure_reason = serializers.CharField()
    latest_pending_toggle_request_id = serializers.IntegerField()


class ProjectMaturityLevelStateSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="maturity_level.id")
    name = serializers.CharField(source="maturity_level.name")
    description = serializers.CharField(source="maturity_level.description")
    maturity_item_states = ProjectMaturityItemStatePreviewSerializer(many=True)


class ProjectMaturityStateSerializer(serializers.Serializer):
    name = serializers.CharField(source="project.maturity_model.name")
    maturity_level_states = ProjectMaturityLevelStateSerializer(many=True)
    achieved_level = serializers.SerializerMethodField()
    passed_enabled_items_count = serializers.IntegerField()

    def get_achieved_level(self, obj: ProjectMaturityState) -> str:
        achieved_level_index = obj.achieved_level_index
        if achieved_level_index is None:
            return "No level achieved"
        else:
            return obj.maturity_level_states[achieved_level_index].maturity_level.name


class ProjectMaturityItemStateEmailSerializer(serializers.Serializer):
    CONTEXT_KEY_PROJECT = "project"

    maturity_model_item = ProjectMaturityItemStatePreviewSerializer(source="*")
    project = serializers.SerializerMethodField()
    dashboard_page_url = serializers.SerializerMethodField()
    notification_settings_page_url = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = kwargs.get('context', {})
        if self.CONTEXT_KEY_PROJECT not in context:
            raise ValueError(f"The context argument containing the '{self.CONTEXT_KEY_PROJECT}' should be given.")

    @property
    def _project(self):
        return self.context[self.CONTEXT_KEY_PROJECT]

    def get_project(self, maturity_item_state: ProjectMaturityItemState):
        return ProjectHyperlinkedReferenceSerializer(self._project).data

    def get_dashboard_page_url(self, maturity_item_state: ProjectMaturityItemState) -> str:
        return f"{settings.FRONTEND_HOST}/project/{self._project.id}/maturity-model/item/{maturity_item_state.maturity_item.id}"

    def get_notification_settings_page_url(self, maturity_item_state: ProjectMaturityItemState) -> str:
        return f"{settings.FRONTEND_HOST}/user/settings"

    def get_subject(self, maturity_item_state: ProjectMaturityItemState) -> str:
        return f"Item {maturity_item_state.maturity_item.code} failed in project: {self._project.name}"


class UserProjectNotifSettingSerializer(serializers.ModelSerializer):
    CONTEXT_KEY_PROJECT_ID = "project_id"
    CONTEXT_KEY_USER = "user"

    project = ProjectSerializer(read_only=True, fields=('id', 'name'))

    class Meta:
        model = UserProjectNotifSetting
        fields = ['project', 'receive_notifications']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for context_key in (
                self.CONTEXT_KEY_PROJECT_ID,
                self.CONTEXT_KEY_USER,
        ):
            if context_key not in self.context:
                raise ValueError(f"The context argument containing the '{context_key}' should be given.")


class DoryEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoryEvaluation
        fields = ['submission_time', 'first_completed_poll_time']
