from unittest import TestCase
from apps.utils.url import get_authorized_url

class BasicAuthUrlGeneratorTest(TestCase):
    TEST_URL = "http://test.com"

    def test_username_can_be_none(self):
        self.assertEqual(
            get_authorized_url(
                url=self.TEST_URL,
                password="password",
            ),
            "http://:password@test.com"
        )

    def test_password_can_be_none(self):
        self.assertEqual(
            get_authorized_url(
                url=self.TEST_URL,
                username="username",
            ),
            "http://username:@test.com"
        )

    def test_username_and_password_both_can_be_none(self):
        self.assertEqual(
            get_authorized_url(
                url=self.TEST_URL,
            ),
            self.TEST_URL
        )
