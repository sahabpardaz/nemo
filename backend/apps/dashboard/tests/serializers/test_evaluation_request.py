from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import serializers
from apps.dashboard.models import (
    EvaluationRequest,
    MaturityModelItem,
    EvaluationType,
    EvaluationReport,
    MaturityModelItemToggleRequest,
    MaturityModelItemToggleApproval,
)
from apps.dashboard.serializers import EvaluationRequestSerializer
from apps.dashboard.tests.utils import setup_basic_environment


class EvaluationRequestSerializerTest(TestCase):
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
        evaluation_request = self._create_evaluation_request()
        self._update_evaluation_request(evaluation_request)
        evaluation_request.refresh_from_db()
        with self.assertRaisesRegex(serializers.ValidationError, r'Only user'):
            self._update_evaluation_request(evaluation_request, applicant=self.another_user)

    def test_only_pending_request_could_be_edited(self):
        evaluation_request = self._create_evaluation_request()
        self._update_evaluation_request(evaluation_request)
        self._create_evaluation_report()
        evaluation_request.refresh_from_db()
        with self.assertRaisesRegex(serializers.ValidationError, r'Only pending requests'):
            self._update_evaluation_request(evaluation_request)

    def test_only_pending_request_could_be_deleted(self):
        evaluation_request = self._create_evaluation_request()
        EvaluationRequestSerializer.validate_on_delete(evaluation_request)
        self._create_evaluation_report()
        evaluation_request.refresh_from_db()
        with self.assertRaises(serializers.ValidationError):
            EvaluationRequestSerializer.validate_on_delete(evaluation_request)

    def test_new_request_can_not_be_created_when_pending_request_exists(self):
        self._create_evaluation_request()
        with self.assertRaises(serializers.ValidationError):
            self._create_evaluation_request()

    def test_new_request_can_not_be_created_when_item_is_disabled(self):
        self._disable_item()
        with self.assertRaises(serializers.ValidationError):
            self._create_evaluation_request()

    def _create_evaluation_request(self) -> EvaluationRequest:
        serializer = EvaluationRequestSerializer(
            data={
                "maturity_model_item": self.manual_mm_item.id,
                "description": "some reason",
            },
            context={
                "project_id": self.env.project.id,
                "user": self.env.user,
            }
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def _disable_item(self):
        mmi_toggle_request = MaturityModelItemToggleRequest.objects.create(
            project=self.env.project,
            maturity_model_item=self.manual_mm_item,
            disable=True,
        )
        MaturityModelItemToggleApproval.objects.create(
            maturity_model_item_toggle_request=mmi_toggle_request,
            approved=True,
        )

    def _update_evaluation_request(self, instance: EvaluationRequest, applicant: User = None):
        if applicant is None:
            applicant = self.env.user

        serializer = EvaluationRequestSerializer(
            instance=instance,
            data={
                "description": "some edited reason",
            },
            context={
                "project_id": self.env.project.id,
                "user": applicant,
            },
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def _create_evaluation_report(self):
        return EvaluationReport.objects.create(
            maturity_model_item=self.manual_mm_item,
            project=self.env.project,
            status=EvaluationReport.STATUS_PASS,
        )
