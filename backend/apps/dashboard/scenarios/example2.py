from apps.dashboard.serializers import MaturityModelSerializer
from apps.dashboard.scenarios.utils import add_json_file_instances
from apps.dashboard.scenarios.serializers import (
    UserSerializer,
    ProjectSerializer,
    EvaluationRequestSerializer,
    EvaluationReportSerializer,
    MaturityModelItemToggleRequestSerializer,
    GoalSerializer,
    ChangeListSerializer,
    DeploymentSerializer,
    ServiceStatusReportSerializer,
    CoverageReportSerializer,
)


def run():
    users = add_json_file_instances(file_path='users1.json', serializer_class=UserSerializer)
    print("users: ", users)
    maturity_models = add_json_file_instances(file_path='maturity_model1399-11-27.json', serializer_class=MaturityModelSerializer)
    print("maturity models: ", maturity_models)
    projects = add_json_file_instances(file_path='projects2.json', serializer_class=ProjectSerializer)
    print("projects: ", projects)
    change_lists = add_json_file_instances(file_path='change_lists2.json', serializer_class=ChangeListSerializer)
    print("change lists: ", change_lists)
    deployments = add_json_file_instances(file_path='deployments2.json', serializer_class=DeploymentSerializer)
    print("deployments: ", deployments)
    service_status_reports = add_json_file_instances(file_path='service_status_reports2.json', serializer_class=ServiceStatusReportSerializer)
    print("service status reports: ", service_status_reports)
    coverage_reports = add_json_file_instances(file_path='coverage_reports2.json', serializer_class=CoverageReportSerializer)
    print("coverage reports: ", coverage_reports)
    goals = add_json_file_instances(file_path='goals2.json', serializer_class=GoalSerializer)
    print("goals: ", goals)
    evaluation_requests = add_json_file_instances(file_path='evaluation_requests2.json', serializer_class=EvaluationRequestSerializer)
    print("evaluation requests: ", evaluation_requests)
    evaluation_reports = add_json_file_instances(file_path='evaluation_reports2.json', serializer_class=EvaluationReportSerializer)
    print("evaluation reports: ", evaluation_reports)
    toggle_requests = add_json_file_instances(file_path='toggle_requests2.json', serializer_class=MaturityModelItemToggleRequestSerializer)
    print("toggle requests: ", toggle_requests)
