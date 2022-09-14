from apps.dashboard.views.authentication import get_user
from apps.dashboard.views.project import (
    ProjectViewSet,
    EvaluationRequestViewSet,
    GoalViewSet,
    SonarProjectViewSet,
    GitlabProjectViewSet,
)
from apps.dashboard.views.maturity_model import (
    MaturityModelViewSet,
    MaturityModelItemToggleRequestViewSet,
)
from apps.dashboard.views.user_project_notif_setting import UserProjectNotifSettingViewSet
from apps.dashboard.views.dory_evaluation import DoryEvaluationViewSet
