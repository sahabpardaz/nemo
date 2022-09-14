from rest_framework.test import APITestCase

from apps.dashboard.tests import utils


class VisitsCountTest(APITestCase):
    def setUp(self) -> None:
        self.env = utils.setup_basic_environment()
        self.client.force_login(self.env.user)

    def test_visits_count_should_increment_on_getting_project(self):
        last_count = self.env.project.hit_count.hits
        self.client.get(f'/v1/dashboard/project/{self.env.project.id}/')
        self.env.project.refresh_from_db()
        self.assertEqual(self.env.project.hit_count.hits, last_count + 1)
