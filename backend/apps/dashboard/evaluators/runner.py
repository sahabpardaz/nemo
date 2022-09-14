import logging
from django.utils import timezone
from apps.dashboard.models import EvaluationReport

logger = logging.getLogger(__name__)


class EvaluatorRunner:
    def __init__(self, projects, maturity_model_items, evaluator_registry):
        self.projects = projects
        self.maturity_model_items = maturity_model_items
        self.evaluator_registry = evaluator_registry

    def run(self):
        for project in self.projects:
            for maturity_model_item in self.maturity_model_items:
                if maturity_model_item.is_disabled(project):
                    logger.debug(f"Item {maturity_model_item.code} is disabled for project {project.name} and no need to be evaluated.")
                    continue

                evaluation_kind = maturity_model_item.evaluation_type.kind
                evaluator = self.evaluator_registry.get(evaluation_kind)
                if not evaluator:
                    logger.info(f"Evaluator for kind {evaluation_kind} not found in registry.")
                    continue

                self.evaluate_and_save_report(evaluator(), project, maturity_model_item)

    def evaluate_and_save_report(self, evaluator, project, maturity_model_item):
        try:
            evaluation_report = evaluator.evaluate(project, maturity_model_item)
            evaluation_report_exists = evaluation_report is not None
            if evaluation_report_exists and evaluation_report.pk is not None:
                evaluation_report.delete()
                raise ValueError(
                    "Evaluators should not insert the evaluation report to database by themselves."
                    "They should only return an unsaved EvaluationReport instance."
                )
        except Exception:
            logger.exception(f"Some errors happened in evaluation of item '{maturity_model_item}' for project '{project}'")
        else:
            if evaluation_report_exists:
                self.add_or_update_evaluation_report(evaluation_report)

    def add_or_update_evaluation_report(self, evaluation_report):
        current_time = timezone.now()
        latest_evaluation_report = EvaluationReport.get_latest(
            project=evaluation_report.project,
            maturity_model_item=evaluation_report.maturity_model_item
        )
        evaluation_report_to_save = evaluation_report
        if (
            latest_evaluation_report is not None
            and self.previous_evaluation_report_can_be_merged_with_the_new_one(
                previous_evaluation_report=latest_evaluation_report,
                new_evaluation_report=evaluation_report,
                current_time=current_time,
            )
        ):
            latest_evaluation_report.latest_evaluation_time = current_time
            evaluation_report_to_save = latest_evaluation_report

        evaluation_report_to_save.save()

    @staticmethod
    def previous_evaluation_report_can_be_merged_with_the_new_one(previous_evaluation_report, new_evaluation_report, current_time):
        return (
            EvaluationReport.is_in_validity_period(previous_evaluation_report, previous_evaluation_report.maturity_model_item, current_time)
            and previous_evaluation_report.logically_equals(new_evaluation_report)
        )
