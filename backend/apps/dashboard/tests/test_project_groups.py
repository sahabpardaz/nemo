from typing import Optional
from django.contrib.auth.models import Group
from django.test import TestCase
from apps.dashboard.tests.utils import setup_basic_environment
from apps.utils.group_and_permission_utils import (
    get_product_managers_of_project_group_name,
    get_developers_of_project_group_name,
    get_team_leaders_of_project_group_name,
)


class ProjectGroupsTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()

    def test_groups_should_be_deleted_after_the_project_being_deleted(self):
        self._assert_groups_of_project_exists(True)
        self.env.project.delete()
        self._assert_groups_of_project_exists(False)

    def test_groups_should_be_renamed_after_the_project_name_being_changed(self):
        old_name = self.env.project.name
        self._assert_groups_of_project_exists(True)
        new_name = 'New' + old_name
        self.env.project.name = new_name
        self.env.project.save()
        self._assert_groups_of_project_exists(False, project_name=old_name)
        self._assert_groups_of_project_exists(True)

    def _assert_groups_of_project_exists(self, must_exist: bool = True, project_name: Optional[str] = None):
        if project_name is None:
            project_name = self.env.project.name

        self.assertEquals(Group.objects.filter(
            name=get_product_managers_of_project_group_name(project_name)
        ).exists(), must_exist)
        self.assertEquals(Group.objects.filter(
            name=get_developers_of_project_group_name(project_name)
        ).exists(), must_exist)
        self.assertEquals(Group.objects.filter(
            name=get_team_leaders_of_project_group_name(project_name)
        ).exists(), must_exist)
