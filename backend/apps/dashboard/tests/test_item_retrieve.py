from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.dashboard.item_retrieve_utils import (
    get_project_maturity_item_state,
)
from apps.dashboard.models.evaluation import EvaluationReport, EvaluationRequest
from apps.dashboard.models.goal import Goal
from apps.dashboard.models.maturity_model import EvaluationType, MaturityModelItem, MaturityModelItemToggleRequest
from apps.dashboard.project_retrieve_utils import ITEM_FAIL_REASON_LAST_EVALUATION_FAILED
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment


class TestItemRetrieve(TestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()
        self.now = timezone.localtime(timezone.now())
        self.evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
            validity_period_days=2,
            checking_period_days=3,
        )
        self.mm_item = MaturityModelItem.objects.create(
            code="C000",
            name="Test Item",
            description="This is a test item",
            evaluation_type=self.evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )

    def test_smoke(self):
        item_state = get_project_maturity_item_state(self.mm_item, self.env.project, self.now)
        self.assertIsNotNone(item_state)
        self.assertEqual(item_state.maturity_item, self.mm_item)

    def test_item_state_props(self):
        with DjangoCurrentTimeMock(self.now - timedelta(days=1)):
            self.evaluation_report = EvaluationReport.objects.create(
                maturity_model_item=self.mm_item,
                project=self.env.project,
                status=EvaluationReport.STATUS_FAIL,
                description="The item is not achieved.",
                expected_value="100",
                current_value="20",
                value_type=MaturityModelItem.VALUE_TYPE_PERCENTAGE,
            )
        pending_evaluation_request = EvaluationRequest.objects.create(
            maturity_model_item=self.mm_item,
            project=self.env.project,
        )
        toggle_request = MaturityModelItemToggleRequest.objects.create(
            maturity_model_item=self.mm_item,
            project=self.env.project,
            disable=True,
            reason="For the sake of test!"
        )
        goal = Goal.objects.create(
            project=self.env.project,
            due_date=self.now + timedelta(days=3),
        )
        goal.maturity_model_items.set([self.mm_item])
        item_state = get_project_maturity_item_state(self.mm_item, self.env.project, self.now)
        self.assertEqual(item_state.maturity_item, self.mm_item)
        self.assertEqual(item_state.maturity_item.evaluation_type, self.evaluation_type)
        self.assertFalse(item_state.is_disabled)
        self.assertEqual(item_state.latest_pending_evaluation_request_id, pending_evaluation_request.pk)
        self.assertEqual(item_state.latest_pending_toggle_request_id, toggle_request.pk)
        self.assertFalse(item_state.is_passed)
        self.assertEqual(item_state.failure_reason, ITEM_FAIL_REASON_LAST_EVALUATION_FAILED)
        self.assertEqual(item_state.latest_evaluation_report, self.evaluation_report)
        self.assertEqual(item_state.closest_goal, goal)
