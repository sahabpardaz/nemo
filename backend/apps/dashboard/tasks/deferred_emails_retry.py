import celery
from celery.utils.log import get_task_logger
from django.conf import settings
from mailer.models import Message

from apps.dashboard import constants

logger = get_task_logger(__name__)


class DeferredEmailsRetry(celery.Task):
    name = constants.TASK_EMAILS_RETRY_DEFERRED

    def run(self, *args, **kwargs):
        if not settings.EMAIL_ENABLED:
            logger.warning("Email is not enabled.")
            return

        count = Message.objects.retry_deferred()
        logger.info(f"{count} email(s) retried.")
