from apps.dashboard.serializers import MaturityModelSerializer
from apps.dashboard.scenarios.utils import add_json_file_instances
from apps.dashboard.scenarios.serializers import (
    UserSerializer,
    ProjectSerializer,
    EvaluationRequestSerializer,
    EvaluationReportSerializer,
    GoalSerializer,
    ChangeListSerializer,
    DeploymentSerializer,
    ServiceStatusReportSerializer,
)


def run():
    users = add_json_file_instances(file_path='users1.json', serializer_class=UserSerializer)
    print("users: ", users)
    maturity_models = add_json_file_instances(file_path='maturity_models1.json', serializer_class=MaturityModelSerializer)
    print("maturity models: ", maturity_models)
    projects = add_json_file_instances(file_path='projects1.json', serializer_class=ProjectSerializer)
    print("projects: ", projects)
    evaluation_requests = add_json_file_instances(file_path='evaluation_requests1.json', serializer_class=EvaluationRequestSerializer)
    print("evaluation requests: ", evaluation_requests)
    evaluation_reports = add_json_file_instances(file_path='evaluation_reports1.json', serializer_class=EvaluationReportSerializer)
    print("evaluation reports: ", evaluation_reports)
    goals = add_json_file_instances(file_path='goals1.json', serializer_class=GoalSerializer)
    print("goals: ", goals)
    change_lists = add_json_file_instances(file_path='change_lists1.json', serializer_class=ChangeListSerializer)
    print("change lists: ", change_lists)
    deployments = add_json_file_instances(file_path='deployments1.json', serializer_class=DeploymentSerializer)
    print("deployments: ", deployments)
    service_status_reports = add_json_file_instances(file_path='service_status_reports1.json', serializer_class=ServiceStatusReportSerializer)
    print("service status reports: ", service_status_reports)
