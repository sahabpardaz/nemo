from datetime import timedelta
from django.utils import timezone
from django.test import TestCase
from rest_framework import serializers
from apps.dashboard.models import Goal, EvaluationType, MaturityModelItem, MaturityModelItemToggleApproval, EvaluationRequest, EvaluationReport
from apps.dashboard.serializers import MaturityModelItemToggleRequestSerializer
from apps.dashboard.tests.utils import setup_basic_environment


class MaturityModelItemToggleTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
            validity_period_days=0,
            checking_period_days=0,
        )
        self.mm_item = MaturityModelItem.objects.create(
            name='Manual',
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        self.context = {
            "project_id": self.env.project.id,
            "applicant": self.env.user,
        }
        self.get_data = lambda disable: {
            "disable": disable,
            "maturity_model_item": self.mm_item.id,
            "reason": "for a few dollars.",
        }

    def test_item_can_not_be_disabled_when_it_has_any_goal(self):
        tomorrow_date = (timezone.now() + timedelta(days=1)).date()
        goal = Goal.objects.create(
            project=self.env.project,
            due_date=tomorrow_date,
        )
        goal.maturity_model_items.add(self.mm_item)
        with self.assertRaises(serializers.ValidationError):
            self._create_toggle_request()

    def test_item_can_not_be_disabled_when_any_pending_request_exists(self):
        self._create_toggle_request()
        with self.assertRaises(serializers.ValidationError):
            self._create_toggle_request()

    def test_item_can_not_be_disabled_when_already_disabled(self):
        toggle_request = self._create_toggle_request()
        MaturityModelItemToggleApproval.objects.create(
            maturity_model_item_toggle_request=toggle_request,
            approved=True,
        )
        with self.assertRaises(serializers.ValidationError):
            self._create_toggle_request()

    def test_fail_evaluation_report_would_be_created_when_disable_toggle_request_approved(self):
        evaluation_request = self._create_evaluation_request()
        toggle_request = self._create_toggle_request()
        MaturityModelItemToggleApproval.objects.create(
            maturity_model_item_toggle_request=toggle_request,
            approved=True,
        )
        evaluation_request.refresh_from_db()
        self.assertEqual(evaluation_request.status, evaluation_request.STATUS_DONE)
        self.assertEqual(evaluation_request.closing_report.status, EvaluationReport.STATUS_FAIL)

    def test_evaluation_report_wont_be_auto_created_when_disable_toggle_request_disapproved(self):
        evaluation_request = self._create_evaluation_request()
        toggle_request = self._create_toggle_request()
        MaturityModelItemToggleApproval.objects.create(
            maturity_model_item_toggle_request=toggle_request,
            approved=False,
        )
        evaluation_request.refresh_from_db()
        self.assertEqual(evaluation_request.status, evaluation_request.STATUS_PENDING)
        self.assertIsNone(evaluation_request.closing_report)

    def _create_toggle_request(self, request_to_disable=True):
        serializer = MaturityModelItemToggleRequestSerializer(data=self.get_data(request_to_disable), context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def _create_evaluation_request(self):
        return EvaluationRequest.objects.create(
            project=self.env.project,
            maturity_model_item=self.mm_item,
            applicant=self.env.user,
        )
