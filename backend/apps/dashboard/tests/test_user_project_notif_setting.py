from django.test import TestCase
from django.contrib.auth.models import Group, User
from apps.dashboard.models.project import Project
from apps.dashboard.tests.utils import setup_basic_environment
from apps.dashboard.models import UserProjectNotifSetting
from apps.utils.group_and_permission_utils import get_developers_of_project_group_name


class UserProjectNotifSettingAutoCreateTest(TestCase):
    def setUp(self) -> None:
        self.maturity_model = setup_basic_environment().maturity_model
        self.user = User.objects.create(username="test2", password="test")
        self.project = Project.objects.create(name="Project #2", maturity_model=self.maturity_model)
        self.group = Group.objects.get(name=get_developers_of_project_group_name(self.project.name))
        self._assert_corresponding_setting_exists(False)

    def _assert_corresponding_setting_exists(self, exists: bool = True):
        self.assertEqual(UserProjectNotifSetting.objects.filter(user=self.user, project=self.project).exists(), exists)

    def test_setting_should_create_when_adding_group_to_user(self):
        self.user.groups.add(self.group)
        self._assert_corresponding_setting_exists()

    def test_setting_should_delete_when_removing_group_from_user(self):
        self.user.groups.add(self.group)
        self.user.groups.remove(self.group)
        self._assert_corresponding_setting_exists(False)

    def test_setting_should_create_when_adding_user_to_group(self):
        self.group.user_set.add(self.user)
        self._assert_corresponding_setting_exists()

    def test_setting_should_delete_when_removing_user_from_group(self):
        self.group.user_set.add(self.user)
        self.group.user_set.remove(self.user)
        self._assert_corresponding_setting_exists(False)

    def test_setting_should_delete_when_clearing_group(self):
        self.group.user_set.add(self.user)
        self.group.user_set.clear()
        self._assert_corresponding_setting_exists(False)

    def test_setting_should_delete_when_clearing_user(self):
        self.group.user_set.add(self.user)
        self.user.groups.clear()
        self._assert_corresponding_setting_exists(False)

    def test_setting_should_create_when_making_user_super(self):
        self.user.is_superuser = True
        self.user.save()
        self._assert_corresponding_setting_exists()

    def test_setting_should_delete_when_making_user_non_super(self):
        self.user.is_superuser = True
        self.user.save()
        self.user.is_superuser = False
        self.user.save()
        self._assert_corresponding_setting_exists(False)
