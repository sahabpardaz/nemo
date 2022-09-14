from django.contrib.auth.models import User, Group
from django.conf import settings
from django.test import TestCase
from django.db import transaction
from rest_framework import status
from rest_framework.test import APIClient
from guardian.shortcuts import assign_perm
from apps.dashboard.models import Project, MaturityModel
from apps.dashboard.tests.utils import setup_basic_environment
from apps.utils.group_and_permission_utils import get_developers_of_project_group_name, \
    get_product_managers_of_project_group_name


class DeveloperAuthorizationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User(username='test', password='test')
        self.user.save()
        self.maturity_model = MaturityModel(name='Quality')
        self.maturity_model.save()
        self.project = Project(name='Project #1', maturity_model_id=self.maturity_model.id, creator_id=self.user.id)
        self.project.save()
        developers = Group.objects.get(
            name=get_developers_of_project_group_name(self.project.name)
        )
        developers.user_set.add(self.user)
        self.project_without_access = Project(name='Project #2', maturity_model_id=self.maturity_model.id, creator_id=self.user.id)
        self.project_without_access.save()
        self.client.force_login(self.user)

    def test_view_project(self):
        response = self.client.get(
            f'{settings.API_URL}/v1/dashboard/project/{self.project.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_to_create_goal(self):
        response = self.client.post(
            f'{settings.API_URL}/v1/dashboard/project/{self.project.id}/goal/',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_nested_related_endpoints(self):
        response = self.client.get(
            f'{settings.API_URL}/v1/devops-metrics/project/{self.project.id}/environment/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_to_view_nested_related_endpoints(self):
        response = self.client.get(
            f'{settings.API_URL}/v1/devops-metrics/project/{self.project_without_access.id}/environment/',
        )
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)


class ProductManagerAuthorizationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User(username='test', password='test')
        self.user.save()
        self.maturity_model = MaturityModel(name='Quality')
        self.maturity_model.save()
        self.project = Project(name='Project #1', maturity_model_id=self.maturity_model.id, creator_id=self.user.id)
        self.project.save()
        product_managers = Group.objects.get(
            name=get_product_managers_of_project_group_name(self.project.name)
        )
        product_managers.user_set.add(self.user)
        self.project_without_access = Project(name='Project #2', maturity_model_id=self.maturity_model.id, creator_id=self.user.id)
        self.project_without_access.save()
        self.client.force_login(self.user)

    def test_create_goal(self):
        response = self.client.post(
            f'{settings.API_URL}/v1/dashboard/project/{self.project.id}/goal/',
        )
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PermissionAssignmentsTest(TestCase):
    PERMISSOIN_CODENAME = 'dashboard.view_project'

    def setUp(self) -> None:
        self.env = setup_basic_environment()
        self.foreign_user = User.objects.create(username="test2", password="test")

    def _transaction_atomic(self):
        # Without transaction.atomic() the swallowed exception will hide the fact that a problem has
        # occured during the DB communication and it leads to unexpected behavior.
        # See 'Avoid catching exceptions inside atomic!' section at:
        #   https://docs.djangoproject.com/en/dev/topics/db/transactions/#django.db.transaction.atomic
        return transaction.atomic()

    def test_user_object_level_permission_can_not_be_set_directly(self):
        with self.assertRaises(AssertionError):
            with self._transaction_atomic():
                assign_perm(self.PERMISSOIN_CODENAME, self.foreign_user, self.env.project)
        self.assertFalse(self.foreign_user.has_perm(self.PERMISSOIN_CODENAME, self.env.project))

    def test_user_model_level_permission_can_not_be_set_directly(self):
        with self.assertRaises(AssertionError):
            with self._transaction_atomic():
                assign_perm(self.PERMISSOIN_CODENAME, self.foreign_user)
        self.assertFalse(self.foreign_user.has_perm(self.PERMISSOIN_CODENAME, self.env.project))
