import logging
from django.db.models import Q
from apps.dashboard.models import EvaluationReport, Project, EvaluationType
from apps.dashboard.evaluators import EvaluatorRunner

logger = logging.getLogger(__name__)


def remove_repeater_evaluation_reports():
    """
        Searches for the burst evaluation reports that are logically equal and can be reduced to just one.
    """
    for project in Project.objects.prefetch_related('maturity_model__levels__items__evaluation_type').all():
        logger.info(f"Project {project.name}")
        for level in project.maturity_model.levels.all():
            for item in level.items.all():
                logger.info(f"\tItem {item.code}")
                previous_evaluation_report: EvaluationReport = None
                for evaluation_report in (
                        EvaluationReport.objects
                            .filter(project=project)
                            .filter(maturity_model_item=item)
                            .filter(~Q(maturity_model_item__evaluation_type__kind=EvaluationType.KIND_MANUAL))
                            .order_by('creation_time')
                            .iterator()
                ):
                    if previous_evaluation_report is None:
                        previous_evaluation_report = evaluation_report
                        continue

                    if EvaluatorRunner.previous_evaluation_report_can_be_merged_with_the_new_one(
                        previous_evaluation_report=previous_evaluation_report,
                        new_evaluation_report=evaluation_report,
                        current_time=evaluation_report.creation_time,
                    ):
                        previous_evaluation_report.latest_evaluation_time = evaluation_report.latest_evaluation_time
                        previous_evaluation_report.save(force_update_latest_evaluation_time=True)
                        evaluation_report.delete()
                    else:
                        previous_evaluation_report = evaluation_report
