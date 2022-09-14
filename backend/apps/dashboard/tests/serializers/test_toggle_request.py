from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import serializers
from apps.dashboard.models import (
    EvaluationRequest,
    MaturityModelItem,
    EvaluationType,
    MaturityModelItemToggleApproval,
)
from apps.dashboard.serializers import MaturityModelItemToggleRequestSerializer
from apps.dashboard.tests.utils import setup_basic_environment


class MaturityModelItemToggleRequestTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        manual_evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
        )
        self.manual_mm_item = MaturityModelItem.objects.create(
            name='Manual',
            evaluation_type=manual_evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        self.another_user = User.objects.create(username='another', password='another')

    def test_only_applicant_of_request_can_edit(self):
        toggle_request = self._create_toggle_request()
        self._update_toggle_request(toggle_request)
        toggle_request.refresh_from_db()
        with self.assertRaisesRegex(serializers.ValidationError, r'Only user'):
            self._update_toggle_request(toggle_request, applicant=self.another_user)

    def test_only_pending_request_could_be_edited(self):
        toggle_request = self._create_toggle_request()
        self._update_toggle_request(toggle_request)
        self._create_toggle_approval(toggle_request)
        toggle_request.refresh_from_db()
        with self.assertRaisesRegex(serializers.ValidationError, r'Only pending requests'):
            self._update_toggle_request(toggle_request)

    def test_only_pending_request_could_be_deleted(self):
        toggle_request = self._create_toggle_request()
        MaturityModelItemToggleRequestSerializer.validate_on_delete(toggle_request)
        self._create_toggle_approval(toggle_request)
        toggle_request.refresh_from_db()
        with self.assertRaises(serializers.ValidationError):
            MaturityModelItemToggleRequestSerializer.validate_on_delete(toggle_request)

    def test_new_request_can_not_be_created_when_pending_request_exists(self):
        self._create_toggle_request()
        with self.assertRaises(serializers.ValidationError):
            self._create_toggle_request()

    def _create_toggle_request(self) -> EvaluationRequest:
        serializer = MaturityModelItemToggleRequestSerializer(
            data={
                "maturity_model_item": self.manual_mm_item.id,
                "reason": "some reason",
                "disable": True,
            },
            context={
                "project_id": self.env.project.id,
                "user": self.env.user,
            }
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def _update_toggle_request(self, instance: EvaluationRequest, applicant: User = None):
        if applicant is None:
            applicant = self.env.user

        serializer = MaturityModelItemToggleRequestSerializer(
            instance=instance,
            data={
                "reason": "some edited reason",
            },
            context={
                "project_id": self.env.project.id,
                "user": applicant,
            },
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def _create_toggle_approval(self, toggle_request):
        return MaturityModelItemToggleApproval.objects.create(
            maturity_model_item_toggle_request=toggle_request,
            approved=True,
        )
