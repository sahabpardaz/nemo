import logging
from typing import Dict, List
from django.conf import settings
from django.contrib.auth.models import Group
from django.template.loader import get_template
from mailer import send_html_mail
from apps.utils.group_and_permission_utils import get_quality_committee_group_name

logger = logging.getLogger(__name__)


def send_email(recipient_list: List[str], message_template_file_path: str, message_html_template_file_path: str, context: Dict):
    if not settings.EMAIL_ENABLED:
        logger.warning("Email is not enabled.")
        return
    message_template = get_template(message_template_file_path)
    message = message_template.render(context)
    message_html_template = get_template(message_html_template_file_path)
    message_html = message_html_template.render(context)
    send_html_mail(
        subject=context['subject'],
        message=message,
        message_html=message_html,
        from_email=settings.EMAIL_SENDER,
        recipient_list=recipient_list,
    )


def send_email_to_quality_committee(message_template_file_path, message_html_template_file_path, context):
    quality_committee = Group.objects.get(name=get_quality_committee_group_name())
    quality_committee_users_emails = quality_committee.user_set.values_list('email', flat=True)
    send_email(quality_committee_users_emails,
               message_template_file_path,
               message_html_template_file_path,
               context)
