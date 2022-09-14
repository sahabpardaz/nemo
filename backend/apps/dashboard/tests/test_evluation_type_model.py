from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.dashboard.models import EvaluationType


class EvaluationTypeModelTest(TestCase):
    def setUp(self):
        EvaluationType.objects.all().delete()

    def test_manual_kinds_can_be_more_than_one(self):
        for i in range(3):
            EvaluationType.objects.create(kind=EvaluationType.KIND_MANUAL)
        self.assertEqual(EvaluationType.objects.filter(kind=EvaluationType.KIND_MANUAL).count(), 3)

    def test_non_manual_kinds_can_not_be_more_than_one(self):
        create_lead_time_evaluation_type = lambda: EvaluationType.objects.create(kind=EvaluationType.KIND_LEAD_TIME)
        create_lead_time_evaluation_type()
        with self.assertRaises(ValidationError):
            create_lead_time_evaluation_type()
