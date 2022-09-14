from typing import Optional

from django.test import TestCase

from apps.dashboard.maturity_state_observer import ProjectsMaturityStateObserver
from apps.dashboard.models import EvaluationType, MaturityModelItem, EvaluationReport
from apps.dashboard.tests.utils import setup_basic_environment
from apps.utils.key_value_storage.key_value_storage import TKey, TValue


class ProjectsMaturityStateObserverTest(TestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()
        self.evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
            validity_period_days=10
        )
        self.mm_items = [
            MaturityModelItem.objects.create(maturity_model_level=self.env.maturity_model_level,
                                             code='1',
                                             name='item1',
                                             evaluation_type=self.evaluation_type),
            MaturityModelItem.objects.create(maturity_model_level=self.env.maturity_model_level,
                                             code='2',
                                             name='item2',
                                             evaluation_type=self.evaluation_type),
        ]
        self.observer = ProjectsMaturityStateObserver()

    def _set_item_status(self, item: MaturityModelItem, passed: bool) -> EvaluationReport:
        return EvaluationReport.objects.create(
            maturity_model_item=item,
            project=self.env.project,
            status=EvaluationReport.STATUS_PASS if passed else EvaluationReport.STATUS_FAIL
        )

    def test_newly_failed_items_should_be_empty_without_previous_observations(self):
        mm_item = self.mm_items[0]
        self._set_item_status(mm_item, passed=False)
        newly_failed_items = self.observer.get_newly_failed_items(self.env.project)
        self.assertEqual(newly_failed_items, [])

    def test_newly_failed_item_is_recognized(self):
        mm_item = self.mm_items[0]
        self._set_item_status(mm_item, passed=True)
        self.observer.update_project_maturity_states()
        self._set_item_status(mm_item, passed=False)
        newly_failed_items = self.observer.get_newly_failed_items(self.env.project)
        self.assertEqual(len(newly_failed_items), 1)
        self.assertEqual(newly_failed_items[0].maturity_item.pk, mm_item.pk)
        self.assertFalse(newly_failed_items[0].is_passed)

    def test_deleting_item_doesnt_cause_error(self):
        mm_item = self.mm_items[0]
        self._set_item_status(mm_item, passed=True)
        self.observer.update_project_maturity_states()
        self._set_item_status(mm_item, passed=False)
        mm_item.delete()
        newly_failed_items = self.observer.get_newly_failed_items(self.env.project)
        self.assertEqual(len(newly_failed_items), 0)

    def test_creating_new_item_is_recognized(self):
        self.observer.update_project_maturity_states()
        mm_item = MaturityModelItem.objects.create(maturity_model_level=self.env.maturity_model_level,
                                             code='tst1',
                                             name='test item 1',
                                             evaluation_type=self.evaluation_type)
        self._set_item_status(mm_item, passed=False)
        newly_failed_items = self.observer.get_newly_failed_items(self.env.project)
        self.assertEqual(len(newly_failed_items), 1)

    def test_non_newly_failed_item_shouldnt_be_reported(self):
        mm_item = self.mm_items[0]
        self.observer.update_project_maturity_states()
        self._set_item_status(mm_item, passed=False)
        newly_failed_items = self.observer.get_newly_failed_items(self.env.project)
        self.assertEqual(len(newly_failed_items), 0)

    def test_multiple_toggle_between_observations_has_no_effect(self):
        mm_item = self.mm_items[0]
        self._set_item_status(mm_item, passed=True)
        self.observer.update_project_maturity_states()
        self._set_item_status(mm_item, passed=False)
        self._set_item_status(mm_item, passed=True)
        newly_failed_items = self.observer.get_newly_failed_items(self.env.project)
        self.assertEqual(len(newly_failed_items), 0)

    def test_changing_project_maturity_state_structure_between_observations_doesnt_crash_observer(self):
        from apps.utils.key_value_storage import InMemoryStorage
        from apps.utils.key_value_storage import KeyValueStorage

        class OldStorage(KeyValueStorage):
            def __init__(self, test_instance: ProjectsMaturityStateObserverTest):
                super().__init__()
                self.test_instance = test_instance
                self._storage = InMemoryStorage()

            def put(self, key: TKey, value: TValue) -> None:
                self._storage.put(key, value)

            def get(self, key: TKey) -> Optional[TValue]:
                return {
                    'project__with_old_label': self._storage.get(key).project,
                    'maturity_level_states__with_old_label':
                        self._storage.get(key).maturity_level_states
                }

        observer_facing_old_state_structure = ProjectsMaturityStateObserver(storage=OldStorage(self))
        observer_facing_old_state_structure.update_project_maturity_states()
        observer_facing_old_state_structure.get_newly_failed_items(self.env.project)
