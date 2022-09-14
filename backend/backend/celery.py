from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from apps.dashboard import constants

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    'periodic_evaluation': {
        'task': constants.TASK_EVALUATE_AUTOMATIC_MM_ITEMS,
        'schedule': settings.AUTO_EVALUATION_INTERVAL,
    },
    'periodic_data_collection': {
        'task': constants.TASK_COLLECT_EXTERNAL_DATA,
        'schedule': settings.AUTO_DATA_COLLECTION_INTERVAL
    },
    'periodic_send_queued_emails': {
        'task': constants.TASK_EMAILS_SEND_QUEUED,
        'schedule': settings.SEND_QUEUED_EMAILS_INTERVAL,
    },
    'periodic_retry_deferred_emails': {
        'task': constants.TASK_EMAILS_RETRY_DEFERRED,
        'schedule': settings.RETRY_DEFERRED_EMAILS_INTERVAL,
    },
    'periodic_project_maturity_state_observation': {
        'task': constants.TASK_OBSERVE_PROJECTS_MATURITY_STATE,
        'schedule': settings.PROJECTS_MATURITY_STATE_OBSERVE_INTERVAL,
    },
    'periodic_gc_of_old_maturity_item_dory_results_files': {
        'task': constants.TASK_MATURITY_ITEM_DORY_RESULTS_FILES_GC,
        'schedule': settings.DORY_EVALUATION_MATURITY_ITEM_RESULTS_FILES_GARABAGE_COLLECTION_PERIOD,
    },
}
