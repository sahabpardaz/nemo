from typing import List
from datetime import timedelta
import celery
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
from apps.dashboard import constants
from apps.dashboard.models import DoryEvaluation

logger = get_task_logger(__name__)


class ModelFileGarbageCollectorError(Exception):
    def __init__(self, object_ids_errored_during_garbage_collection: List[int]) -> None:
        super().__init__("Some files failed to delete at garbage collection."
            f"Errored report ids: {object_ids_errored_during_garbage_collection}")


class FileGarbageCollectionSummaryInfo:
    def __init__(self, total_files_for_gc: int) -> None:
        self.total_files_for_gc = total_files_for_gc
        self.errored_report_ids = []
        self.total_reclaimed_bytes = 0
        self.non_existing_files = 0

    def __str__(self) -> str:
        return (f"Garbage collection summary:\n"
                f"\tTotal files discovered for GC: {self.total_files_for_gc}\n"
                f"\tItems failed to GC: {len(self.errored_report_ids)}\n"
                f"\tNon-existing files: {self.non_existing_files}\n"
                f"\tTotal reclaimed space: {self.total_reclaimed_bytes} bytes"
                )


class DoryEvaluationMaturityItemDoryResultsFileGarbageCollector(celery.Task):
    name = constants.TASK_MATURITY_ITEM_DORY_RESULTS_FILES_GC

    def run(self, *args, **kwargs):
        objects_to_remove_file_from = self._get_objects_to_remove_file_from()
        summary_info = FileGarbageCollectionSummaryInfo(len(objects_to_remove_file_from))
        for object_to_remove_file_from in objects_to_remove_file_from:
            try:
                try:
                    file_size = self.get_file_field(object_to_remove_file_from).size
                except FileNotFoundError:
                    file_size = 0
                    summary_info.non_existing_files += 1
                self.get_file_field(object_to_remove_file_from).delete()
                summary_info.total_reclaimed_bytes += file_size
            except Exception:
                summary_info.errored_report_ids.append(object_to_remove_file_from.pk)
                logger.exception(
                    f"An error occured during deletion of the {self.file_field_name} "
                    f"from {object_to_remove_file_from.__class__.__name__} (id={object_to_remove_file_from.pk})"
                )
        logger.info(summary_info)
        if summary_info.errored_report_ids:
            raise ModelFileGarbageCollectorError(summary_info.errored_report_ids)

    @property
    def file_field_name(self):
        return 'maturity_item_dory_results_file'

    def get_file_field(self, object):
        return getattr(object, self.file_field_name)

    def _get_objects_to_remove_file_from(self):
        return (DoryEvaluation.objects
            .filter(
                first_completed_poll_time__lt=timezone.now() - timedelta(days=settings.DORY_EVALUATION_MATURITY_ITEM_RESULTS_FILES_RETENTION_DAYS)
            )
            .exclude(maturity_item_dory_results_file='')
        )
