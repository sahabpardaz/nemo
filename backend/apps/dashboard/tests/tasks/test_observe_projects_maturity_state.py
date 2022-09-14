from unittest import mock
from django.test import TestCase
from apps.dashboard.models.maturity_model import EvaluationType, MaturityModelItem
from apps.dashboard.models.project_maturity_state import ProjectMaturityItemState
from apps.dashboard.models.user_project_notif_setting import UserProjectNotifSetting

from apps.dashboard.tests.utils import setup_basic_environment
from apps.dashboard.tasks import InformUsersAboutRecentlyFailedItems
from apps.dashboard.maturity_state_observer import ProjectsMaturityStateObserver


class ProjectsMaturityObservationTaskTest(TestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()
        self.inform_users_task = InformUsersAboutRecentlyFailedItems()
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_LEAD_TIME,
            checking_period_days=1,
            validity_period_days=1,
        )
        self.mm_item = MaturityModelItem.objects.create(
            code="T000",
            name="Test",
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
            acceptable_value=2,
            acceptable_value_type=MaturityModelItem.VALUE_TYPE_SECONDS,
        )
        self.newly_failed_items = [
            ProjectMaturityItemState(
                maturity_item=self.mm_item,
                is_disabled=False,
                is_passed=False,
            )
        ]

    def _mock_get_newly_failed_items(self):
        mock_context_manager = mock.patch.object(ProjectsMaturityStateObserver,
                                                 'get_newly_failed_items')
        return mock_context_manager

    def test_failed_item_email_sends(self):
        setting = UserProjectNotifSetting.objects.get(user=self.env.user, project=self.env.project)
        setting.receive_notifications = True
        setting.save()
        from apps.dashboard.tasks import inform_users_about_recently_failed_items
        with mock.patch.object(inform_users_about_recently_failed_items, 'send_email') as mocked_send_email, \
                self._mock_get_newly_failed_items() as mocked_get_newly_failed_items:
            mocked_get_newly_failed_items.return_value = self.newly_failed_items
            self.inform_users_task.run()
            mocked_send_email.assert_called_once()

    def test_failed_item_email_doesnt_send_to_users_who_disabled_notif(self):
        from apps.dashboard.tasks import inform_users_about_recently_failed_items
        with mock.patch.object(inform_users_about_recently_failed_items, 'send_email') as mocked_send_email, \
                self._mock_get_newly_failed_items() as mocked_get_newly_failed_items:
            mocked_get_newly_failed_items.return_value = self.newly_failed_items
            self.inform_users_task.run()
            mocked_send_email.assert_not_called()
