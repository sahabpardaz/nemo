import logging
from django.conf import settings
from django.dispatch import receiver
from request_profiler.signals import request_profile_complete


logger = logging.getLogger(__name__)


@receiver(request_profile_complete)
def on_request_profile_complete(instance, **kwargs):
    profiler = instance
    if profiler.elapsed > settings.MAX_PROCESS_TIME_OF_REQUESTS_TO_ALERT_IN_SECONDS:
        logger.error(
            f"Request exceeded max process time. Request Profiler Record Id: {profiler.pk}"
        )
    else:
        profiler.cancel()
