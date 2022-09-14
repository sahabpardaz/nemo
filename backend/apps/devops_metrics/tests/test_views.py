import datetime
import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import pytz
from rest_framework import status
from rest_framework.test import APITestCase
from apps.dashboard.tests.utils import setup_basic_environment
from apps.devops_metrics.models import ChangeList, ServiceStatusReport
from apps.dashboard.models import Project, Environment, MaturityModel

logger = logging.getLogger(__name__)

class EnvironmentTest(APITestCase):
    def setUp(self):
        Project.objects.all().delete()
        self.maturity_model = MaturityModel(name='Quality')
        self.maturity_model.save()
        self.user = User(username='test', password='test')
        self.user.save()
        self.project = Project(name='Project #1', maturity_model_id=self.maturity_model.id, creator_id=self.user.id)
        self.project.save()

    def test_create(self):
        data = {'name': 'Environment #1'}
        response = self.client.post('/v1/devops-metrics/project/%d/environment/' % self.project.id, data,
                                    format='json', **{'HTTP_NEMO_PROJECT_TOKEN': self.project.auth_token.key})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.project.environments.get().name, 'Environment #1')


class ChangeListTest(APITestCase):
    def setUp(self):
        Project.objects.all().delete()
        self.maturity_model = MaturityModel(name='Quality')
        self.maturity_model.save()
        self.user = User(username='test', password='test')
        self.user.save()
        self.project = Project(name='Project #1', maturity_model_id=self.maturity_model.id, creator_id=self.user.id)
        self.project.save()

    def test_create(self):
        data = {'change_list_id': '1',
                'commit_hash': 'd29ada62de494ad991400275c775cbd0ba38bd4c',
                'time': '2019-10-24T00:12'}
        response = self.client.post('/v1/devops-metrics/project/%d/changelist/' % self.project.id, data,
                                    format='json', **{'HTTP_NEMO_PROJECT_TOKEN': self.project.auth_token.key})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.project.changelist_set.get().commit_hash, 'd29ada62de494ad991400275c775cbd0ba38bd4c')

    def test_create_with_bad_commit_hash(self):
        data = {'change_list_id': '1',
                'commit_hash': '1',
                'time': '2019-10-24T00:12'}
        response = self.client.post('/v1/devops-metrics/project/%d/changelist/' % self.project.id, data,
                                    format='json', **{'HTTP_NEMO_PROJECT_TOKEN': self.project.auth_token.key})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeploymentTest(APITestCase):
    def setUp(self):
        Project.objects.all().delete()
        self.maturity_model = MaturityModel(name='Quality')
        self.maturity_model.save()
        self.user = User(username='test', password='test')
        self.user.save()
        self.project = Project(name='Project #1', maturity_model_id=self.maturity_model.id, creator_id=self.user.id)
        self.project.save()
        self.environment = Environment(name='Env #1', project=self.project)
        self.environment.save()
        self.change_list = ChangeList(project=self.project, change_list_id=1, commit_hash='1',
                                      time=datetime.datetime(year=2000, month=1, day=1, hour=14, minute=30, tzinfo=pytz.UTC))
        self.change_list.save()

    def test_create(self):
        data = {'commit_hash': self.change_list.commit_hash,
                'status': 'P',
                'time': '2019-10-24T00:12'}
        response = self.client.post('/v1/devops-metrics/project/%d/environment/%d/deployment/' % (self.project.id, self.environment.id),
                                    data, format='json', **{'HTTP_NEMO_PROJECT_TOKEN': self.project.auth_token.key})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.project.changelist_set.get().deployment_set.get().status, 'P')


class ReportTest(APITestCase):
    def setUp(self):
        Project.objects.all().delete()
        self.maturity_model = MaturityModel(name='Quality')
        self.maturity_model.save()
        self.user = User(username='test', password='test')
        self.user.save()
        self.project = Project(name='Project #1', maturity_model_id=self.maturity_model.id, creator_id=self.user.id)
        self.project.save()
        self.environment = Environment(name='Env #1', project=self.project)
        self.environment.save()

    def test_create(self):
        data = {'status': 'U',
                'time': '2019-10-24T00:12'}
        response = self.client.post('/v1/devops-metrics/project/%d/environment/%d/report/' % (self.project.id, self.environment.id),
                                    data, format='json', **{'HTTP_NEMO_PROJECT_TOKEN': self.project.auth_token.key})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.project.environments.get().servicestatusreport_set.get().status, 'U')


class DailyMetricTest(APITestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()

    def test_computation_for_day_should_include_data_of_whole_day_long(self):
        day = timezone.now().date()
        local_timezone = pytz.timezone(settings.TIME_ZONE)
        early_datetime = datetime.datetime.combine(day, datetime.time.min.replace(tzinfo=local_timezone))
        late_datetime = datetime.datetime.combine(day, datetime.time.max.replace(tzinfo=local_timezone))
        ServiceStatusReport.objects.create(
            environment=self.env.environment,
            status=ServiceStatusReport.STATUS_DOWN,
            time=early_datetime
        )
        ServiceStatusReport.objects.create(
            environment=self.env.environment,
            status=ServiceStatusReport.STATUS_UP,
            time=late_datetime
        )
        url = f'/v1/devops-metrics/project/{self.env.project.pk}/environment/{self.env.environment.pk}/metric/time-to-restore/'
        params = f'period_start_date={day.year}-{day.month}-{day.day}'
        params += f'&period_end_date={day.year}-{day.month}-{day.day}'
        params += f'&checking_period_days=2'
        response = self.client.get(f'{url}?{params}', **{'HTTP_NEMO_PROJECT_TOKEN': self.env.project.auth_token.key})
        logger.debug(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data_points = response.json()
        self.assertEqual(len(data_points), 1)
        self.assertEqual(response.json()[0].get('value'), (late_datetime - early_datetime).seconds)
