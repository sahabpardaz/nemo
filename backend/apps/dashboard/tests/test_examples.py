from django.test import TestCase
from apps.dashboard import scenarios


class ExampleTest(TestCase):
    def test_example1(self):
        scenarios.example1()

    def test_example2(self):
        scenarios.example2()
