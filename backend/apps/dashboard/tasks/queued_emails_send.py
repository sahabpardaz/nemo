import celery
from celery.utils.log import get_task_logger
from django.conf import settings
from mailer.engine import send_all

from apps.dashboard import constants

logger = get_task_logger(__name__)


class QueuedEmailsSend(celery.Task):
    name = constants.TASK_EMAILS_SEND_QUEUED

    def run(self, *args, **kwargs):
        if not settings.EMAIL_ENABLED:
            logger.warning("Email is not enabled.")
            return

        send_all()
        logger.info("All queued emails sent.")
