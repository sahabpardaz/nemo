import logging
from django.core.management.base import BaseCommand
from apps.custom_scripts.evaluation_report_pruning import remove_repeater_evaluation_reports
from apps.dashboard.models import EvaluationReport

logger = logging.getLogger('apps.custom_scripts')


class Command(BaseCommand):
    help = (
        'Searches for the bursts evaluation reports that logically equal and can be reduced to just one and deletes them.'
    )

    def handle(self, *args, **options):
        logger.info("Started.")
        evaluation_reports_count_before_script = EvaluationReport.objects.count()
        logger.info(f"Current evaluation reports count is {evaluation_reports_count_before_script}")
        remove_repeater_evaluation_reports()
        evaluation_reports_count_after_script = EvaluationReport.objects.count()
        logger.info(
            f"Operation completed successfully."
            f"About {evaluation_reports_count_after_script - evaluation_reports_count_before_script} evaluation reports deleted."
        )
