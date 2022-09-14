from datetime import datetime, timedelta
import os
from django.test import TestCase
from django.utils import timezone
from django.conf import settings
from apps.dashboard.models import DoryEvaluation
from apps.dashboard.tests.utils import DjangoCurrentTimeMock, setup_basic_environment
from apps.dashboard.tasks import DoryEvaluationMaturityItemDoryResultsFileGarbageCollector


class DoryEvaluationMaturityItemDoryResultsFileGarbageCollectorTest(TestCase):
    def setUp(self) -> None:
        self.env = setup_basic_environment()
        self.now = timezone.now()
        self.gc_task = DoryEvaluationMaturityItemDoryResultsFileGarbageCollector()

    def test_non_old_files_arent_deleted(self):
        dory_evaluation = self._create_dory_evaluation_with_file()
        self.gc_task.run()
        self.assertTrue(os.path.exists(dory_evaluation.maturity_item_dory_results_file.path))

    def test_old_files_are_deleted(self):
        dory_evaluation = self._create_old_dory_evaluation_with_file()
        self.gc_task.run()
        self.assertFalse(os.path.exists(dory_evaluation.maturity_item_dory_results_file.path))

    def test_already_deleted_files_dont_error_on_next_gc(self):
        self._create_old_dory_evaluation_with_file()
        self.gc_task.run()
        try:
            self.gc_task.run()
        except Exception as e:
            self.fail(f"An error occured during second run of GC. Error: {e}")

    def test_non_existing_old_file_dont_crash_gc(self):
        dory_evaluation = self._create_old_dory_evaluation_with_file()
        dory_evaluation = self._create_old_dory_evaluation_with_file()
        os.remove(dory_evaluation.maturity_item_dory_results_file.path)
        try:
            self.gc_task.run()
        except Exception as e:
            self.fail(f"An error occured during the run of GC. Error: {e}")

    def _create_dory_evaluation_with_file(self, time: datetime = None) -> DoryEvaluation:
        if time is None:
            time = self.now
        with DjangoCurrentTimeMock(time):
            dory_evaluation = DoryEvaluation(
                project=self.env.project,
                submission_time=time,
                first_completed_poll_time=time,
            )
            dory_evaluation.set_maturity_item_dory_results([])
            dory_evaluation.save()
        return dory_evaluation

    def _create_old_dory_evaluation_with_file(self) -> DoryEvaluation:
        return self._create_dory_evaluation_with_file(self.now - timedelta(days=settings.DORY_EVALUATION_MATURITY_ITEM_RESULTS_FILES_RETENTION_DAYS + 10))
