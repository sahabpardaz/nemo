import celery
from celery.utils.log import get_task_logger

from apps.dashboard import constants
from apps.dashboard.data_collectors.registry import data_collector_registry


logger = get_task_logger(__name__)


class ExternalDataCollection(celery.Task):
    name = constants.TASK_COLLECT_EXTERNAL_DATA

    def run(self, *args, **kwargs):
        logger.info(f"Starting extrenal data collection with collectors: {[d.__name__ for d in data_collector_registry]}")
        for collector in data_collector_registry:
            try:
                collector().collect_and_save_data()
            except Exception:
                logger.exception(f"External data collector of type '{collector}' encountered an exception.")
