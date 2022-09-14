from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from apps.dashboard.tests.utils import DjangoCurrentTimeMock

class NowTimeMockTest(TestCase):
    def test_can_mock_django_timezone_now_with_custom_time(self):
        now_mock = datetime(year=2000, month=1, day=1, hour=1, minute=1, second=1, microsecond=1)
        with DjangoCurrentTimeMock(now_mock):
            now = timezone.now()
        self.assertEqual(now, now_mock)
