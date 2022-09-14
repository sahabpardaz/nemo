import logging
from datetime import timedelta
from typing import Optional
from django.utils import timezone
from django.test import TestCase
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment
from apps.dashboard.models import (
    Project,
    EvaluationType,
    EvaluationReport,
    MaturityModelItem,
)
from apps.dashboard.evaluators.runner import EvaluatorRunner
from apps.dashboard.evaluators.base import Evaluator


class EvaluatorMock(Evaluator):
    def evaluate(self, project: Project, maturity_model_item: MaturityModelItem) -> Optional[EvaluationReport]:
        return EvaluationReport(
            project=project,
            maturity_model_item=maturity_model_item,
            status=EvaluationReport.STATUS_PASS,
        )


class EvaluatorThatSavesAndReturnsEvaluationReportMock(Evaluator):
    def evaluate(self, project: Project, maturity_model_item: MaturityModelItem) -> Optional[EvaluationReport]:
        evaluation_report = EvaluationReport(
            project=project,
            maturity_model_item=maturity_model_item,
            status=EvaluationReport.STATUS_PASS,
        )
        evaluation_report.save()
        return evaluation_report


class EvaluatorRunnerTest(TestCase):
    def setUp(self):
        test_env = setup_basic_environment()
        self.evaluation_kind = EvaluationType.KIND_LEAD_TIME  # Random non-manual kind
        self.item_validity_period_days = 1
        evaluation_type = EvaluationType.objects.create(
            kind=self.evaluation_kind,
            validity_period_days=self.item_validity_period_days,
        )
        mm_item = MaturityModelItem.objects.create(
            code='TEST',
            name='TEST',
            evaluation_type=evaluation_type,
            maturity_model_level=test_env.maturity_model_level,
        )
        self.projects = [test_env.project]
        self.maturity_model_items = [mm_item]
        evaluator_registry = {
            self.evaluation_kind: EvaluatorMock,
        }
        self.evaluator_runner = EvaluatorRunner(
            self.projects,
            self.maturity_model_items,
            evaluator_registry,
        )

    def test_happy_path(self):
        self.evaluator_runner.run()

        self.assertEqual(EvaluationReport.objects.count(), 1)

    def test_duplicate_evaluation_should_not_create_a_new_report(self):
        self.evaluator_runner.run()
        self.evaluator_runner.run()

        self.assertEqual(EvaluationReport.objects.count(), 1)

    def test_evaluators_can_not_return_a_saved_evaluation_report(self):
        evaluator_runner = EvaluatorRunner(
            projects=self.projects,
            maturity_model_items=self.maturity_model_items,
            evaluator_registry={
                self.evaluation_kind: EvaluatorThatSavesAndReturnsEvaluationReportMock,
            },
        )
        with self.assertLogs(level=logging.ERROR) as logs:
            evaluator_runner.run()
            self.assertEqual(EvaluationReport.objects.count(), 0)
            self.assertIn("only return an unsaved EvaluationReport instance", logs.output[-1])

    def test_duplicate_evaluation_should_create_a_new_report_when_the_latest_expired(self):
        self.evaluator_runner.run()
        with DjangoCurrentTimeMock(timezone.now() + timedelta(days=self.item_validity_period_days + 1)):
            self.evaluator_runner.run()

        self.assertEqual(EvaluationReport.objects.count(), 2)
