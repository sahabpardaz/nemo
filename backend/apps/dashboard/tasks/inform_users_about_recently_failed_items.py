import celery
from celery.utils.log import get_task_logger
from django.conf import settings

from apps.dashboard.mailer import send_email
from apps.dashboard.maturity_state_observer import ProjectsMaturityStateObserver
from apps.dashboard.models.user_project_notif_setting import UserProjectNotifSetting
from apps.utils.key_value_storage.cache_storage import CacheStorage
from apps.dashboard.serializers import ProjectMaturityItemStateEmailSerializer
from apps.dashboard import constants
from apps.dashboard.models.project import Project

logger = get_task_logger(__name__)


class InformUsersAboutRecentlyFailedItems(celery.Task):
    name = constants.TASK_OBSERVE_PROJECTS_MATURITY_STATE

    def run(self, *args, **kwargs):
        logger.info("Started")
        observer = ProjectsMaturityStateObserver(storage=CacheStorage(settings.CACHE_NAME_FILE_BASED))
        for project in Project.objects.all():
            newly_failed_items = observer.get_newly_failed_items(project)
            logger.info(f"Newly failed items of project {project.name}:\n{newly_failed_items}")
            if len(newly_failed_items) > 0:
                recipient_emails = UserProjectNotifSetting.objects \
                    .filter(project=project) \
                    .filter(receive_notifications=True) \
                    .exclude(user__email__isnull=True) \
                    .exclude(user__email__exact='') \
                    .values_list('user__email', flat=True)
                logger.info(f"Recipients: {recipient_emails}")
                if len(recipient_emails) > 0:
                    for item in newly_failed_items:
                        serializer = ProjectMaturityItemStateEmailSerializer(
                            item,
                            context={ProjectMaturityItemStateEmailSerializer.CONTEXT_KEY_PROJECT: project}
                        )
                        logger.info(f"Sending mail for item {item} ...")
                        send_email(recipient_emails,
                                   'email/item_failure_report.txt',
                                   'email/item_failure_report.html',
                                   serializer.data)
        logger.info("Going to update maturity states ...")
        observer.update_project_maturity_states()
        logger.info("Finished")
