from django.test import TestCase
from apps.dashboard.models import MaturityModel, Project, Environment
from apps.devops_metrics.models import ChangeList, Deployment
from apps.custom_scripts.deployment_pruning import remove_deployments_of_changelists_except_latest_ones


class Test(TestCase):
    def setUp(self):
        maturity_model = MaturityModel.objects.create(name='test-mm')
        self.project = Project.objects.create(
            name='test',
            maturity_model=maturity_model,
        )
        self.environment = Environment.objects.create(
            project=self.project,
            name="default test env",
        )
        self.project.default_environment = self.environment
        self.project.save()
        acceptable_deployments = []
        # Changelist 1
        change_list_1 = self._create_change_list(1)
        self._create_deployment(change_list_1, Deployment.STATUS_FAIL)
        acceptable_deployments.append(
            self._create_deployment(change_list_1, Deployment.STATUS_PASS)
        )
        self._create_deployment(change_list_1, Deployment.STATUS_FAIL)

        # Changelist 2
        change_list_2 = self._create_change_list(2)
        self._create_deployment(change_list_2, Deployment.STATUS_FAIL)
        acceptable_deployments.append(
            self._create_deployment(change_list_2, Deployment.STATUS_FAIL)
        )

        # Changelist 3
        change_list_3 = self._create_change_list(3)
        self._create_deployment(change_list_3, Deployment.STATUS_PASS)
        acceptable_deployments.append(
            self._create_deployment(change_list_3, Deployment.STATUS_PASS)
        )

        self.acceptable_deployment_ids = [d.id for d in acceptable_deployments]

    def _create_deployment(self, change_list, status):
        return Deployment.objects.create(
            environment=self.environment,
            change_list=change_list,
            status=status,
        )

    def _create_change_list(self, unique_id):
        return ChangeList.objects.create(
            project=self.project,
            commit_hash=unique_id,
            change_list_id=unique_id,
        )

    def test_that_keeps_only_acceptable_deployments(self):
        remove_deployments_of_changelists_except_latest_ones(project_id=self.project.id)
        deployment_ids = Deployment.objects.filter(change_list__project=self.project).values_list('id', flat=True)
        self.assertCountEqual(
            self.acceptable_deployment_ids,
            deployment_ids
        )
