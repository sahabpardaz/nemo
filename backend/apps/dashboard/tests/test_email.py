from django.test import TestCase
from django.contrib.auth.models import Group
from mailer.models import Message
from apps.dashboard.tests.utils import setup_basic_environment
from apps.dashboard.models import EvaluationRequest, EvaluationType, MaturityModelItem, MaturityModelItemToggleRequest
from apps.utils.group_and_permission_utils import get_quality_committee_group_name


class EmailTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        evaluation_type = EvaluationType.objects.create(kind=EvaluationType.KIND_MANUAL)
        self.mm_item = MaturityModelItem.objects.create(
            name='Manual',
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        quality_committee = Group.objects.get(name=get_quality_committee_group_name())
        quality_committee.user_set.add(self.env.user)
        self.email_test_settings = {
            'EMAIL_ENABLED': True,
            'EMAIL_SENDER': 'test@test.test',
            'FRONTEND_HOST': 'http://localhost',
        }

    def test_email_created_after_evaluation_request_created(self):
        with self.settings(**self.email_test_settings):
            EvaluationRequest.objects.create(
                maturity_model_item=self.mm_item,
                project=self.env.project,
                applicant=self.env.user,
            )
            self.assertEqual(1, Message.objects.non_deferred().count())

    def test_email_created_after_toggle_request_created(self):
        with self.settings(**self.email_test_settings):
            MaturityModelItemToggleRequest.objects.create(
                maturity_model_item=self.mm_item,
                project=self.env.project,
                applicant=self.env.user,
                disable=True,
            )
            self.assertEqual(1, Message.objects.non_deferred().count())
