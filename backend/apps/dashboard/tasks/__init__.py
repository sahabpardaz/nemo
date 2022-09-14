from backend.celery import app
from apps.dashboard.tasks.automatic_mm_items_evaluation import AutomaticMMItemsEvaluation
from apps.dashboard.tasks.deferred_emails_retry import DeferredEmailsRetry
from apps.dashboard.tasks.dory_evaluation_maturity_item_dory_results_file_gc import DoryEvaluationMaturityItemDoryResultsFileGarbageCollector
from apps.dashboard.tasks.external_data_collection import ExternalDataCollection
from apps.dashboard.tasks.inform_users_about_recently_failed_items import InformUsersAboutRecentlyFailedItems
from apps.dashboard.tasks.queued_emails_send import QueuedEmailsSend

task_classes = (
    DoryEvaluationMaturityItemDoryResultsFileGarbageCollector,
    AutomaticMMItemsEvaluation,
    ExternalDataCollection,
    QueuedEmailsSend,
    DeferredEmailsRetry,
    InformUsersAboutRecentlyFailedItems,
)

for task_class in task_classes:
    app.register_task(task_class)
