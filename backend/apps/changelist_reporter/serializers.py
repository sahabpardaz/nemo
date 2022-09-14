from rest_framework import serializers
from django.conf import settings
from apps.dashboard.models import Project
from apps.devops_metrics.models import ChangeList
from apps.dashboard.constants import DEFAULT_BRANCH_MAX_LENGTH


class GitlabDevopsmetricsReporterSerializer(serializers.Serializer):
    project_id = serializers.PrimaryKeyRelatedField(source='project', queryset=Project.objects.all())
    merge_requests_merged_after = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        # Validate project access token
        access_token = self.context["headers"].get(settings.PROJECT_TOKEN_HEADER)
        project = attrs.get('project')
        validate_project_access_token(project, access_token)

        return attrs


class GitlabMergeRequestWebHookObjectAttributesSerializer(serializers.Serializer):
    iid = serializers.IntegerField()
    target_branch = serializers.CharField(max_length=DEFAULT_BRANCH_MAX_LENGTH)
    state = serializers.CharField()
    action = serializers.CharField()


class GitlabMergeRequestWebHookProjectSerializer(serializers.Serializer):
    id = serializers.IntegerField()


def validate_project_access_token(project, access_token):
    if access_token is None:
        raise serializers.ValidationError(f'"{settings.PROJECT_TOKEN_HEADER}" is not set in your headers')

    if access_token != project.auth_token.key:
        raise serializers.ValidationError(f"Inavlid token for project {project.id}")


class GitlabMergeRequestReportSerializer(serializers.Serializer):
    commit_hash = serializers.CharField(max_length=ChangeList.COMMIT_HASH_MAX_LENGTH)

    def validate(self, attrs):
        # Find nemo project that belong to this request
        project_access_token = self.context["headers"].get(settings.PROJECT_TOKEN_HEADER)

        if not Project.objects.filter(auth_token__key=project_access_token).exists():
            raise serializers.ValidationError('Project with this access token not found.')

        return attrs
