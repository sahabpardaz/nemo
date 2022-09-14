from django.test import TestCase
from apps.utils.key_value_storage import InMemoryStorage

class InMemoryStorageTest(TestCase):
    def setUp(self) -> None:
        self.storage = InMemoryStorage()

    def test_item_can_be_retreived_after_put(self):
        self.storage.put("key", "value")
        self.assertEqual(self.storage.get("key"), "value")

    def test_not_found_key_results_in_none_value(self):
        self.assertIsNone(self.storage.get("not exitstent key"))

    def test_has_key_returns_true_when_found(self):
        self.storage.put("key", "value")
        self.assertTrue(self.storage.get("key"))

    def test_has_key_returns_false_when_not_found(self):
        self.assertFalse(self.storage.get("key"))
