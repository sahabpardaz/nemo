import logging
from datetime import datetime
from django.db import transaction
from django.db.models import Q, Subquery
from apps.dashboard.models import Project
from apps.devops_metrics.models import Deployment

logger = logging.getLogger(__name__)


def remove_deployments_of_changelists_except_latest_ones(project_id: int, period_start: datetime = None, period_end: datetime = None):
    """
    This method keeps last passed deployment of all changelists in given time period if exists and if not keeps last failed deployment
    """
    project = Project.objects.get(id=project_id)
    with transaction.atomic():
        deployments_to_keep = Deployment.objects.filter(change_list__project=project)
        if period_start is not None:
            deployments_to_keep = deployments_to_keep.filter(change_list__time__gte=period_start)

        if period_end is not None:
            deployments_to_keep = deployments_to_keep.filter(change_list__time__lt=period_end)

        deployments_to_keep = deployments_to_keep \
            .order_by('change_list_id', '-status', '-time') \
            .distinct('change_list_id') \
            .values_list('id', flat=True)

        Deployment.objects \
            .filter(change_list__project=project) \
            .filter(~Q(id__in=Subquery(deployments_to_keep))) \
            .delete()

        logger.info(
            f"All deployments of changelists except latest ones for project {project.name} "
            f"from {period_start} to {period_end} deleted."
        )
