from datetime import date, timedelta
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from apps.utils.serializer_utils import (
    set_one_to_many_composition,
    set_one_to_one_reverse_composition,
)
from apps.dashboard.models import (
    MaturityModel,
    MaturityModelItem,
    Project,
    Environment,
    SonarProject,
    GitRepo,
    CoverageReport,
    EvaluationRequest,
    EvaluationReport,
    MaturityModelItemToggleRequest,
    Goal,
)
from apps.devops_metrics.models import (
    ChangeList,
    Deployment,
    ServiceStatusReport,
)
from apps.utils.validation_utils import check_for_duplicate_values_in_unique_fields


class UserByUsernameField(serializers.SlugRelatedField):
    def __init__(self, queryset=User.objects, **kwargs):
        super().__init__(slug_field='username', queryset=queryset, **kwargs)


class ProjectByNameField(serializers.SlugRelatedField):
    def __init__(self, queryset=Project.objects, **kwargs):
        super().__init__(slug_field='name', queryset=queryset, **kwargs)


class MaturityModelByNameField(serializers.SlugRelatedField):
    def __init__(self, queryset=MaturityModel.objects, **kwargs):
        super().__init__(slug_field='name', queryset=queryset, **kwargs)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username', 'password', 'email',
            'is_staff', 'is_active', 'is_superuser',
            'first_name', 'last_name',
            #'groups', 'user_permissions',
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # Override
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class EnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = ['name', 'description']

    # Override
    def validate(self, attrs):
        project = attrs.get('project', None)
        # This kind of check is only useful when the parent is also set and already saved in DB.
        # It does not check the uniqueness among unsaved siblings.
        if project:
            name = attrs['name']
            if Environment.objects.filter(project=project, name=name).exists():
                raise serializers.ValidationError('An environment with this name already exists in this project.')
        return attrs


class SonarProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SonarProject
        fields = ['project_key', 'api_base_url', 'auth_token']


class GitRepoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitRepo
        fields = [
            'git_http_url',
            'default_branch',
            'username', 'password',
            'git_ecosystem',
            'changelist_collection_enabled',
        ]


class ProjectSerializer(serializers.ModelSerializer):
    creator = UserByUsernameField()
    maturity_model = MaturityModelByNameField()
    groups = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Group.objects,
        many=True,
        required=False,
        allow_null=True,
    )
    environments = EnvironmentSerializer(
        many=True,
    )
    default_environment = serializers.CharField(
        required=False,
        allow_null=True,
    )
    sonar_projects = SonarProjectSerializer(
        source='sonarprojects',
        required=False,
        many=True,
    )
    git_repo = GitRepoSerializer(
        source='gitrepo',
        required=False,
    )

    class Meta:
        model = Project
        fields = [
            'name',
            'maturity_model',
            'creator', 'groups',
            'environments', 'default_environment',
            'sonar_projects',
            'git_repo',
        ]

    def validate_environments(self, value):
        # This check is useful when the data is not persisted yet.
        check_for_duplicate_values_in_unique_fields(value, "name")
        return value

    # Override
    def validate(self, attrs):
        default_environment_name = attrs.get('default_environment', None)
        if default_environment_name is not None: # Checking validity of default_environment_name
            validation_error = serializers.ValidationError(f"There is no environment with name '{default_environment_name}'.")
            environments_data = attrs.get('environments', None)
            project = getattr(self, 'instance', None)
            if project and environments_data is None: # Update mode with old environments
                if not project.environments.filter(name=default_environment_name).exists():
                    raise validation_error
            else:
                if environments_data is None:
                    environments_data = []
                if not any(env_data.get('name', None) == default_environment_name
                            for env_data in environments_data):
                    raise validation_error
        return attrs

    # Override
    def create(self, validated_data):
        environments_data = validated_data.pop('environments', [])
        default_environment_name = validated_data.pop('default_environment', None)
        sonar_projects_data = validated_data.pop('sonarprojects', [])
        git_repo_data = validated_data.pop('gitrepo', None)
        project = Project.objects.create(**validated_data)
        set_one_to_many_composition(
            parent_instance=project,
            child_list_data=environments_data,
            child_serializer=self.fields['environments'],
            parent_name='project',
            children_name='environments',
        )
        if default_environment_name is not None:
            project.default_environment = project.environments.get(name=default_environment_name)
            project.save()
        set_one_to_many_composition(
            parent_instance=project,
            child_list_data=sonar_projects_data,
            child_serializer=self.fields['sonar_projects'],
            parent_name='nemo_project',
            children_name='sonarprojects',
        )
        set_one_to_one_reverse_composition(
            parent_instance=project,
            child_data=git_repo_data,
            child_serializer=self.fields['git_repo'],
            parent_name='nemo_project',
            child_name='gitrepo',
        )
        return project


class EnvironmentReferenceSerializer(serializers.ModelSerializer):
    project = ProjectByNameField()

    class Meta:
        model = Environment
        fields = ['project', 'name']

    # Override
    def validate(self, attrs):
        project = attrs.get('project')
        name = attrs.get('name')
        try:
            return project.environments.get(name=name)
        except Environment.DoesNotExist:
            raise serializers.ValidationError(f"Project '{project}' has no environment with name '{name}'.")


class MaturityModelItemReferenceSerializer(serializers.ModelSerializer):
    maturity_model = MaturityModelByNameField()

    class Meta:
        model = MaturityModelItem
        fields = ['maturity_model', 'code']

    # Override
    def validate(self, attrs):
        maturity_model = attrs.get('maturity_model')
        code = attrs.get('code')
        try:
            return maturity_model.items.get(code=code)
        except MaturityModelItem.DoesNotExist:
            raise serializers.ValidationError(f"Maturity model '{maturity_model}' has no item with code '{code}'.")


class EvaluationRequestSerializer(serializers.ModelSerializer):
    project = ProjectByNameField()
    maturity_model_item = MaturityModelItemReferenceSerializer()
    applicant = UserByUsernameField()
    # closing_report = ...

    class Meta:
        model = EvaluationRequest
        fields = [
            'project',
            'maturity_model_item',
            'description',
            'applicant',
            'time',
            'status',
            # 'closing_report',
        ]
        read_only_fields = [
            'status',
            # 'closing_report',
        ]


class EvaluationReportSerializer(serializers.ModelSerializer):
    project = ProjectByNameField()
    maturity_model_item = MaturityModelItemReferenceSerializer()
    reporter = UserByUsernameField(required=False)

    class Meta:
        model = EvaluationReport
        fields = [
            'project',
            'maturity_model_item',
            'status',
            'reporter',
            'description',
            'current_value',
            'expected_value', 'value_type',
            'creation_time', 'last_update_time',
        ]
        read_only_fields = [
            'expected_value', 'value_type',
            'creation_time', 'last_update_time',
        ]

    # Override
    def create(self, validated_data):
        evaluation_report = EvaluationReport.create_new(**validated_data)
        evaluation_report.save()
        return evaluation_report


class MaturityModelItemToggleRequestSerializer(serializers.ModelSerializer):
    project = ProjectByNameField()
    maturity_model_item = MaturityModelItemReferenceSerializer()
    applicant = UserByUsernameField()

    class Meta:
        model = MaturityModelItemToggleRequest
        fields = [
            'project',
            'maturity_model_item',
            'applicant',
            'disable',
            'reason',
            'creation_time',
        ]


class RelativeDateField(serializers.Field):
    """
    A date relative to now.
    """
    # Override
    def to_representation(self, value: date) -> int:
        remaining: timedelta = value - date.today()
        return remaining.days

    # Override
    def to_internal_value(self, data: int) -> date:
        remaining: timedelta = timedelta(days=data)
        return date.today() + remaining


class GoalSerializer(serializers.ModelSerializer):
    project = ProjectByNameField()
    maturity_model_items = MaturityModelItemReferenceSerializer(many=True)
    due_date = RelativeDateField()
    creator = UserByUsernameField()

    class Meta:
        model = Goal
        fields = [
            'project',
            'maturity_model_items',
            'due_date',
            'creator',
            'creation_time', 'last_update_time',
        ]
        read_only_fields = [
            'creation_time', 'last_update_time',
        ]

    # Override
    def create(self, validated_data):
        maturity_model_items = validated_data.pop('maturity_model_items', [])
        goal = Goal.objects.create(**validated_data)
        goal.maturity_model_items.set(maturity_model_items)
        return goal


class ChangeListSerializer(serializers.ModelSerializer):
    project = ProjectByNameField()

    class Meta:
        model = ChangeList
        fields = [
            'project',
            'change_list_id',
            'commit_hash',
            'time',
            'title',
        ]

    # Override
    def validate(self, attrs):
        project = attrs.get('project')
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


class DeploymentSerializer(serializers.ModelSerializer):
    environment = EnvironmentReferenceSerializer()
    change_list_id = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
        max_length=ChangeList.CHANGE_LIST_ID_MAX_LENGTH,
    )

    class Meta:
        model = Deployment
        fields = [
            'environment',
            'change_list_id',
            'status',
            'time',
        ]

    # Override
    def validate(self, attrs):
        environment = attrs.get('environment')
        project = environment.project
        change_list_id = attrs.pop('change_list_id')
        try:
            attrs['change_list'] = ChangeList.objects.get(project=project, change_list_id=change_list_id)
        except ChangeList.DoesNotExist:
            raise serializers.ValidationError(f"Project '{project}' does not have a change list with id='{change_list_id}'.")
        return attrs


class ServiceStatusReportSerializer(serializers.ModelSerializer):
    environment = EnvironmentReferenceSerializer()

    class Meta:
        model = ServiceStatusReport
        fields = [
            'environment',
            'status',
            'time',
        ]


class CoverageReportSerializer(serializers.ModelSerializer):
    project = ProjectByNameField()

    class Meta:
        model = CoverageReport
        fields = [
            'project',
            'coverage_type',
            'version',
            'value',
            'creation_time',
            'last_update_time',
            'creator',
        ]

    def validate(self, attrs):
        CoverageReport.validate_version_and_coverage_type_uniqueness_in_project(
            old_instance=self.instance if self.instance else None,
            new_project=attrs.get('project'),
            new_coverage_type=attrs.get('coverage_type'),
            new_version=attrs.get('version'),
            validation_error_class=serializers.ValidationError,
        )
        return attrs
