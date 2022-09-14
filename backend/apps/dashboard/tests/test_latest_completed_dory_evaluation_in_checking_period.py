from datetime import timedelta, datetime
import logging
from django.utils import timezone
from rest_framework.test import APITestCase
from apps.dashboard.models import MaturityModelItem, EvaluationType, DoryEvaluation
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment


logger = logging.getLogger(__name__)

class CompletedDoryEvaluationsInCheckingPeriodTest(APITestCase):
    """Tests the 'get_completed_evaluations_in_checking_period' static method in 'DoryEvaluation' class."""

    def setUp(self) -> None:
        self.env = setup_basic_environment()
        evaluation_type = EvaluationType.objects.create(
            kind=EvaluationType.KIND_MANUAL,
            validity_period_days=10,
            checking_period_days=10,
        )
        self.mm_item = MaturityModelItem.objects.create(
            name='Manual',
            evaluation_type=evaluation_type,
            maturity_model_level=self.env.maturity_model_level,
        )
        self.now = timezone.make_aware(datetime(2000, 1, 1))

    def test_non_completed_dory_evaluation_should_not_be_returned(self):
        with DjangoCurrentTimeMock(self.now):
            DoryEvaluation.objects.create(
                project=self.env.project,
                submission_id="1",
            )
        self.assertEquals(
            len(DoryEvaluation.get_completed_evaluations_in_checking_period(
                project=self.env.project,
                checking_period_days=self.mm_item.evaluation_type.checking_period_days,
                current_time=self.now + timedelta(hours=1),
            )), 0
        )

    def test_dory_evaluation_with_submission_before_checking_period_should_not_be_returned(self):
        DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="1",
            submission_time=self.now - timedelta(days=11),
            first_completed_poll_time=self.now - timedelta(days=11) + timedelta(hours=1),
        )
        self.assertEquals(
            len(DoryEvaluation.get_completed_evaluations_in_checking_period(
                project=self.env.project,
                checking_period_days=self.mm_item.evaluation_type.checking_period_days,
                current_time=self.now,
            )), 0
        )

    def test_multiple_dory_evaluations_in_checking_period_should_be_returned(self):
        DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="1",
            submission_time=self.now - timedelta(days=1),
            first_completed_poll_time=self.now - timedelta(days=1) + timedelta(hours=1),
        )
        DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="2",
            submission_time=self.now - timedelta(days=2),
            first_completed_poll_time=self.now - timedelta(days=2) + timedelta(hours=1),
        )
        self.assertEquals(
            len(DoryEvaluation.get_completed_evaluations_in_checking_period(
                project=self.env.project,
                checking_period_days=self.mm_item.evaluation_type.checking_period_days,
                current_time=self.now,
            )), 2
        )

    def test_dory_evaluations_not_completely_in_checking_period_should_not_be_returned(self):
        DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="1",
            submission_time=self.now - timedelta(days=self.mm_item.evaluation_type.checking_period_days + 1),
            first_completed_poll_time=self.now - timedelta(days=self.mm_item.evaluation_type.checking_period_days - 1),
        )
        DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="2",
            submission_time=self.now - timedelta(days=1),
            first_completed_poll_time=self.now - timedelta(days=1) + timedelta(hours=1),
        )
        DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="3",
            submission_time=self.now - timedelta(days=1),
            first_completed_poll_time=self.now + timedelta(days=1),
        )
        completed_evaluations_in_checking_period = DoryEvaluation.get_completed_evaluations_in_checking_period(
            project=self.env.project,
            checking_period_days=self.mm_item.evaluation_type.checking_period_days,
            current_time=self.now,
        )
        self.assertEquals(len(completed_evaluations_in_checking_period), 1)
        self.assertEquals(completed_evaluations_in_checking_period[0].submission_id, "2")

    def test_dory_evaluations_be_returned_ordered_by_lowest_to_highest_submission_time(self):
        DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="1",
            submission_time=self.now - timedelta(days=2),
            first_completed_poll_time=self.now - timedelta(days=2) + timedelta(hours=1),
        )
        DoryEvaluation.objects.create(
            project=self.env.project,
            submission_id="2",
            submission_time=self.now - timedelta(days=1),
            first_completed_poll_time=self.now - timedelta(days=1) + timedelta(hours=1),
        )
        completed_evaluations_in_checking_period = DoryEvaluation.get_completed_evaluations_in_checking_period(
            project=self.env.project,
            checking_period_days=self.mm_item.evaluation_type.checking_period_days,
            current_time=self.now,
        )
        self.assertEquals(len(completed_evaluations_in_checking_period), 2)
        self.assertEquals(completed_evaluations_in_checking_period.last().submission_id, "2")
