from django.urls import include, path
from rest_framework import routers
from rest_framework_extensions.routers import NestedRouterMixin
from apps.dashboard.views import (
    ProjectViewSet,
    EvaluationRequestViewSet,
    get_user,
    GoalViewSet,
    SonarProjectViewSet,
    GitlabProjectViewSet,
    MaturityModelViewSet,
    MaturityModelItemToggleRequestViewSet,
    UserProjectNotifSettingViewSet,
    DoryEvaluationViewSet,
)
from apps.dashboard.views.coverage_report import CoverageReportViewSet
from apps.dashboard.views.project import EvaluationReportViewSet
from apps.dashboard.views.visits_count import get_total_visits_count
from apps.devops_metrics.constants import PARENT_LOOKUP_PROJECT


class NestedDefaultRouter(NestedRouterMixin, routers.DefaultRouter):
    pass


router = NestedDefaultRouter()

router.register('maturity-model', MaturityModelViewSet, basename='maturity-model')

project_router = router.register('project', ProjectViewSet, basename='project')

# Pattern : project/{id}/evaluation/
project_router.register('evaluation', EvaluationRequestViewSet,
                        basename='project-evaluation',
                        parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : project/{id}/maturity-model-item-constraint/
project_router.register('maturity-model-item-constraint', MaturityModelItemToggleRequestViewSet,
                        basename='project-maturity-model-item-constraint',
                        parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : project/{id}/goal/
project_router.register('goal', GoalViewSet,
                        basename='project-goal',
                        parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : project/{id}/coverage-report/
project_router.register('coverage-report',
                        CoverageReportViewSet,
                        basename='project-coverage-report',
                        parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : project/{id}/dory-evaluation/
project_router.register('dory-evaluation',
                        DoryEvaluationViewSet,
                        basename='project-dory-evaluation',
                        parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : project/{id}/integration/sonar
project_router.register('integration/sonar', SonarProjectViewSet,
                        basename='project-integration-sonar',
                        parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : project/{id}/integration/gitlab-project
project_router.register('integration/gitlab-project', GitlabProjectViewSet,
                        basename='project-integration-gitlab-project',
                        parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : project/{id}/item/{id}/evaluation-report/
project_router.register(f'item/(?P<{EvaluationReportViewSet.URL_PARAM_MM_ITEM_ID}>\d+)/evaluation-report',
                        EvaluationReportViewSet,
                        basename='evaluation-report',
                        parents_query_lookups=[PARENT_LOOKUP_PROJECT])

# Pattern : user/settings/notification/project/{id}/
router.register('user/settings/notification/project', UserProjectNotifSettingViewSet, basename='user-settings-notification-project')

urlpatterns = [
    path('', include(router.urls)),
    path('user/', get_user, name='get_user'),
    path('visits-count/', get_total_visits_count, name='get_total_visits_count'),
]
