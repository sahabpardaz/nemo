from django.test import TestCase
from seal.exceptions import UnsealedAttributeAccess
from apps.dashboard.tests.utils import setup_basic_environment
from apps.dashboard.models import CoverageReport


class SealedModelTest(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()
        # An arbitrary model inherited from SealableModel
        CoverageReport.objects.create(
            project=self.env.project,
            value=10,
            coverage_type=CoverageReport.TYPE_OVERALL,
        )

    def test_error_should_raise_when_a_field_is_not_preloaded_in_a_sealed_object(self):
        with self.assertRaises(UnsealedAttributeAccess):
            CoverageReport.objects.only('coverage_type').seal()[0].value
