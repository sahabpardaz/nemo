from django.test import TestCase

from apps.utils.group_and_permission_utils import ROLE_DEVELOPER, ROLE_PRODUCT_MANAGER, ROLE_TEAM_LEADER, get_project_name_from_group_name


class GroupAndPermissionUtilsTest(TestCase):
    def test_project_name_should_be_none_if_role_is_miscellaneous(self):
        project_name = get_project_name_from_group_name(f"my-project [some-random-role]")
        self.assertIsNone(project_name)

    def test_project_name_should_be_none_if_group_pattern_is_miscellaneous(self):
        project_name = get_project_name_from_group_name(f"my-project some custom group")
        self.assertIsNone(project_name)

    def test_get_project_name_from_group_name_of_different_roles(self):
        for role in [ROLE_TEAM_LEADER, ROLE_DEVELOPER, ROLE_PRODUCT_MANAGER]:
            project_name = get_project_name_from_group_name(f"my-project [{role}]")
            self.assertEqual(project_name, "my-project")
