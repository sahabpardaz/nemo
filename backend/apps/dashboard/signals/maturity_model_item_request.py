from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.dashboard.models import MaturityModelItemToggleRequest
from apps.utils.signal_utils import with_action
from apps.dashboard.serializers import ToggleRequestEmailSerializer
from apps.dashboard.mailer import send_email_to_quality_committee
from apps.dashboard.signals._shared_utils import get_email_context


@receiver([post_save, post_delete], sender=MaturityModelItemToggleRequest)
@with_action
def send_toggle_request_change_email_to_quality_committee(action, instance, *args, **kwargs):
    send_email_to_quality_committee(
        message_template_file_path='email/toggle_request.txt',
        message_html_template_file_path='email/toggle_request.html',
        context=get_email_context(action, instance, ToggleRequestEmailSerializer)
    )
