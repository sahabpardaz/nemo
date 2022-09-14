from django.test import TestCase
from apps.dashboard.models import EvaluationType, MaturityModelItem
from apps.dashboard.models.evaluation import EvaluationReport
from apps.dashboard.serializers import ProjectMaturityStateSerializer
from apps.dashboard.tests.utils import setup_basic_environment
from apps.dashboard.project_retrieve_utils import get_project_maturity_state, get_project_with_related_fields


class TestProjectRetrieve(TestCase):
    def setUp(self):
        self.env = setup_basic_environment()

    def _retrieve_project_maturity_state(self, project_pk):
        project = get_project_with_related_fields(project_pk)
        return ProjectMaturityStateSerializer(
            instance=get_project_maturity_state(project=project)
        ).data

    def _generate_manual_maturity_model_item(self, count=1, start_number=0):
        evaluation_type = EvaluationType.objects.create(kind=EvaluationType.KIND_MANUAL)
        for i in range(count):
            unique_key = str(start_number + i)
            MaturityModelItem(
                name=f"item {unique_key}",
                code=unique_key,
                evaluation_type=evaluation_type,
                maturity_model_level=self.env.maturity_model_level,
            ).save()

    def test_number_of_database_queries_is_constant(self):
        expected_queries_count = 11
        self._generate_manual_maturity_model_item(count=30)
        with self.assertNumQueries(expected_queries_count):
            self._retrieve_project_maturity_state(self.env.project.pk)

        self._generate_manual_maturity_model_item(count=40, start_number=30)
        with self.assertNumQueries(expected_queries_count):
            self._retrieve_project_maturity_state(self.env.project.pk)

    def test_item_is_passed_in_maturity_state(self):
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
            validity_period_days=10
        )
        mm_item = MaturityModelItem.objects.create(
            maturity_model_level=self.env.maturity_model_level,
            name="1",
            code="T001",
            evaluation_type=evaluation_type
        )
        EvaluationReport.objects.create(
            project=self.env.project,
            maturity_model_item=mm_item,
            status=EvaluationReport.STATUS_PASS,
        )
        maturity_state = get_project_maturity_state(self.env.project)
        self.assertEqual(maturity_state.maturity_level_states[0].maturity_item_states[0].maturity_item.pk, mm_item.pk)
        self.assertTrue(maturity_state.maturity_level_states[0].maturity_item_states[0].is_passed)
