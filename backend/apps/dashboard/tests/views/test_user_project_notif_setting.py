from rest_framework import status
from rest_framework.test import APITestCase
from apps.dashboard.models import (
    Project,
    Environment,
    UserProjectNotifSetting,
)
from apps.dashboard.tests.utils import setup_basic_environment


class UserProjectNotifSettingViewSetTest(APITestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        self.client.force_login(self.env.user)

    def test_notification_settings_count_should_be_equal_to_the_projects_that_user_has_access(self):
        # Create another project that user has no access to it
        project = Project.objects.create(
            name='Project #2',
            maturity_model=self.env.maturity_model,
            creator=self.env.user,
        )
        environment = Environment.objects.create(project=project, name="Default Environment")
        project.default_environment = environment
        project.save()

        response = self.client.get('/v1/dashboard/user/settings/notification/project/')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 1)

    def test_activation_and_deactivation_the_notification_settings(self):
        self._change_and_assert_receive_notification_settings(False)
        self._change_and_assert_receive_notification_settings(True)

    def _change_and_assert_receive_notification_settings(self, receive_notifications):
        response = self.client.patch(
            f'/v1/dashboard/user/settings/notification/project/{self.env.project.id}/',
            data={'receive_notifications': receive_notifications}
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        settings = UserProjectNotifSetting.objects.get(project=self.env.project, user=self.env.user)
        self.assertEquals(settings.receive_notifications, receive_notifications)
