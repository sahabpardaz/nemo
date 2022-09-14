from datetime import timedelta
import logging
from django.test import TestCase
from django.utils import timezone
from apps.dashboard.models.goal import Goal
from apps.dashboard.models.maturity_model import EvaluationType, MaturityModelItem
from apps.dashboard.models.project_maturity_state import ProjectMaturityItemState, ProjectMaturityLevelState
from apps.dashboard.tests.utils import setup_basic_environment
from apps.dashboard.serializers import ProjectMaturityStateSerializer
from apps.dashboard.models import ProjectMaturityState


class ProjectMaturityStateSerializerTest(TestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()

    def test_project_maturity_state_fields_should_be_present(self):
        project_maturity_state = ProjectMaturityState(self.env.project, [])
        serialized_maturity_state = ProjectMaturityStateSerializer(instance=project_maturity_state).data
        self.assertEqual(serialized_maturity_state["name"],
                         self.env.maturity_model.name)
        self.assertEqual(serialized_maturity_state["maturity_level_states"], [])
        self.assertIsNotNone(serialized_maturity_state["achieved_level"])
        self.assertEqual(serialized_maturity_state["passed_enabled_items_count"], 0)

    def test_maturity_level_state_fields_should_be_present(self):
        project_maturity_state = ProjectMaturityState(self.env.project,
                                             [
                                                ProjectMaturityLevelState(
                                                    self.env.maturity_model_level,
                                                    []
                                                )
                                            ])
        serialized_maturity_state = ProjectMaturityStateSerializer(instance=project_maturity_state).data
        maturity_level_states = serialized_maturity_state["maturity_level_states"]
        self.assertEqual(len(maturity_level_states), 1)
        maturity_level_state = maturity_level_states[0]
        self.assertEqual(maturity_level_state["id"], self.env.maturity_model_level.pk)
        self.assertEqual(maturity_level_state["name"], self.env.maturity_model_level.name)
        self.assertEqual(maturity_level_state["description"], self.env.maturity_model_level.description)

    def test_maturity_item_state_light_fields_should_be_present(self):
        evaluation_type = EvaluationType.objects.create(kind=EvaluationType.KIND_MANUAL)
        mm_items = [
            MaturityModelItem.objects.create(
                maturity_model_level=self.env.maturity_model_level,
                name="1",
                code="T001",
                evaluation_type=evaluation_type
            ),
            MaturityModelItem.objects.create(
                maturity_model_level=self.env.maturity_model_level,
                name="2",
                code="T002",
                evaluation_type=evaluation_type
            ),
        ]
        goal = Goal.objects.create(
            project=self.env.project,
            due_date=(timezone.now() + timedelta(days=10)).date()
        )
        goal.maturity_model_items.set(mm_items[:1])
        maturity_item_states = [
            ProjectMaturityItemState(
                mm_items[0],
                is_disabled=False,
                is_passed=True,
                closest_goal=goal,
                latest_pending_evaluation_request_id=None,
                latest_pending_toggle_request_id=None
            ),
            ProjectMaturityItemState(
                mm_items[1],
                is_disabled=True,
                is_passed=False,
                closest_goal=None,
                latest_pending_evaluation_request_id=None,
                latest_pending_toggle_request_id=None
            ),
        ]
        project_maturity_state = ProjectMaturityState(self.env.project,
                                             [
                                                ProjectMaturityLevelState(
                                                    self.env.maturity_model_level,
                                                    maturity_item_states
                                                )
                                            ])
        serialized_maturity_state = ProjectMaturityStateSerializer(instance=project_maturity_state).data
        items = serialized_maturity_state["maturity_level_states"][0]["maturity_item_states"]
        self.assertEqual(len(items), 2)
        for i, item_data in enumerate(items):
            logging.debug(f"Asserting fields of item_data {i}")
            self.assertEqual(item_data["maturity_item"]["id"], maturity_item_states[i].maturity_item.pk)
            self.assertEqual(item_data["maturity_item"]["code"], maturity_item_states[i].maturity_item.code)
            self.assertEqual(item_data["maturity_item"]["name"], maturity_item_states[i].maturity_item.name)
            self.assertEqual(item_data["maturity_item"]["evaluation_type"]["kind"], maturity_item_states[i].maturity_item.evaluation_type.kind)
            self.assertEqual(item_data["disabled"], maturity_item_states[i].is_disabled)
            self.assertEqual(item_data["latest_pending_evaluation_request_id"], maturity_item_states[i].latest_pending_evaluation_request_id)
            self.assertEqual(item_data["is_passed"], maturity_item_states[i].is_passed)
            if maturity_item_states[i].closest_goal is None:
                self.assertIsNone(item_data["closest_goal"])
            else:
                self.assertIsNotNone(item_data["closest_goal"])
