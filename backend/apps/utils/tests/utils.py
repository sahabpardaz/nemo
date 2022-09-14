from django.test import TestCase
from django.conf import settings
from apps.utils.os_utils import run_cmd


class TestCaseUsingUtilsModels(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        run_cmd(['python3', './manage.py', 'makemigrations', 'utils'],
                cwd=settings.BASE_DIR,
                raise_on_non_zero_code=True)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        run_cmd(['rm', '-rf', './apps/utils/migrations/'],
                cwd=settings.BASE_DIR,
                raise_on_non_zero_code=True)
