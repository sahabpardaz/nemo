from django.urls import include, path
from rest_framework import routers
from rest_framework_extensions.routers import NestedRouterMixin
from apps.devops_metrics import views
from apps.devops_metrics.constants import PARENT_LOOKUP_PROJECT, PARENT_LOOKUP_ENVIRONMENT


class NestedDefaultRouter(NestedRouterMixin, routers.DefaultRouter):
    pass


router = NestedDefaultRouter()

# Pattern : project/{id}
project_router = router.register('project', views.ProjectViewSet)

# Pattern : project/{id}/changelist/
project_router.register('changelist', views.ChangeListViewSet,
                        basename='project-changelist',
                        parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : project/{id}/environment/
project_environment_router = project_router.register('environment', views.EnvironmentViewSet,
                                                     basename='project-environments',
                                                     parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : project/{id}/environment/{i}/deployment
project_environment_router.register('deployment', views.DeploymentViewSet,
                                    basename='project-environment-deployment',
                                    parents_query_lookups=[PARENT_LOOKUP_PROJECT, PARENT_LOOKUP_ENVIRONMENT])

# Pattern : project/{id}/environment/{i}/report
project_environment_router.register('report', views.ServiceStatusReportViewSet,
                                    basename='project-environment-report',
                                    parents_query_lookups=[PARENT_LOOKUP_PROJECT, PARENT_LOOKUP_ENVIRONMENT])

urlpatterns = [
    path('', include(router.urls)),
]
