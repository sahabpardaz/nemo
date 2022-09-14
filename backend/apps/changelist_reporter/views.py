from django.conf import settings
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_202_ACCEPTED
from apps.changelist_reporter.serializers import GitlabDevopsmetricsReporterSerializer, \
    GitlabMergeRequestReportSerializer
from apps.changelist_reporter.tasks import \
    get_gitlab_changelists_and_report_to_devopsmetrics, add_gitlab_merge_request_report
from apps.dashboard.models import Project


@permission_classes((AllowAny,))
class Gitlab(ViewSet):
    serializer_class = GitlabDevopsmetricsReporterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'headers': request.headers})
        serializer.is_valid(raise_exception=True)

        project = serializer.validated_data.get('project')
        merge_requests_merged_after = serializer.validated_data.get('merge_requests_merged_after')

        get_gitlab_changelists_and_report_to_devopsmetrics.delay(
            nemo_project_id=project.id,
            gitlab_project_id=project.version_control.project_id,
            gitlab_project_default_branch=project.version_control.default_branch,
            gitlab_project_token=project.version_control.token,
            gitlab_project_merge_request_merged_after=merge_requests_merged_after
        )

        return Response(
            {'message': 'Changelists will be received form GitLab and will be sent to DevOpsMetrics soon.'},
            status=HTTP_200_OK
        )


@permission_classes((AllowAny,))
class GitlabMergeRequestReport(ViewSet):
    """
    This API would help Gitlab projects report changelists easily just by sending project API token and commit hash
    """
    serializer_class = GitlabMergeRequestReportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'headers': request.headers})
        serializer.is_valid(raise_exception=True)
        nemo_project_access_token = request.headers.get(settings.PROJECT_TOKEN_HEADER)
        merge_request_commit_hash = serializer.validated_data.get('commit_hash')

        nemo_project = Project.objects.get(auth_token__key=nemo_project_access_token)

        add_gitlab_merge_request_report.delay(
            nemo_project_id=nemo_project.id,
            gitlab_project_token=nemo_project.version_control.token,
            gitlab_project_id=nemo_project.version_control.project_id,
            gitlab_project_default_branch=nemo_project.version_control.default_branch,
            gitlab_merge_request_commit_hash=merge_request_commit_hash
        )

        return Response(
            {
                'message': (
                    f'Merge request with commit hash {merge_request_commit_hash} '
                    'will be reported to DevOpsMetrics soon.'
                )
            },
            status=HTTP_202_ACCEPTED
        )
