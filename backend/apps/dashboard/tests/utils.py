from datetime import datetime
from django.contrib.auth.models import User, Group
import mock

from apps.dashboard.models import (
    EvaluationReport,
    Project,
    MaturityModel,
    MaturityModelLevel,
)
from apps.dashboard.models.coverage_report import CoverageReport
from apps.dashboard.models.devops_metrics import Environment
from apps.utils.group_and_permission_utils import get_developers_of_project_group_name


class BasicTestEnvironment:
    def __init__(self, maturity_model: MaturityModel, maturity_model_level: MaturityModelLevel, user: User, project: Project, environment: Environment):
        self.maturity_model = maturity_model
        self.maturity_model_level = maturity_model_level
        self.user = user
        self.project = project
        self.environment = environment


def setup_basic_environment() -> BasicTestEnvironment:
    CoverageReport.objects.all().delete()
    EvaluationReport.objects.all().delete()
    Project.objects.all().delete()
    MaturityModel.objects.all().delete()
    maturity_model = MaturityModel.objects.create(name='Quality')
    maturity_model_level = MaturityModelLevel.objects.create(name='Level 1',
                                                             maturity_model=maturity_model)
    user = User.objects.create(username='test', password='test', email='test@fake.com')
    project = Project.objects.create(name='Project #1',
                                     maturity_model=maturity_model,
                                     creator_id=user.id)
    environment = Environment.objects.create(project=project, name="Default Environment")
    project.default_environment = environment
    project.save()
    developers = Group.objects.get(
        name=get_developers_of_project_group_name(project.name)
    )
    developers.user_set.add(user)

    return BasicTestEnvironment(maturity_model,
                                maturity_model_level,
                                user,
                                project,
                                environment)

class DjangoCurrentTimeMock:
    def __init__(self, now: datetime):
        self.now = now
        self.now_mock_resource = mock.patch('django.utils.timezone.now')

    def __enter__(self):
        self.now_mock = self.now_mock_resource.__enter__()
        self.now_mock.return_value = self.now
        return self.now_mock

    def __exit__(self, exc_type, exc_value, traceback):
        self.now_mock_resource.__exit__(exc_type, exc_value, traceback)
