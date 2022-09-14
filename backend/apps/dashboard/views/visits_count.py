from django.conf import settings
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from apps.dashboard.models import Project


@api_view(["GET"])
@permission_classes((AllowAny,))
def get_total_visits_count(request):
    projects = Project.objects.all()
    checking_period_days = request.query_params.get(
        'checking_period_days',
        settings.NEMO_HITCOUNT_DEFAULT_CHECKING_PERIOD_DAYS)
    if type(checking_period_days) == str and not checking_period_days.isnumeric():
        return Response({'error': 'checking_period_days should be numeric'},
                        status=HTTP_400_BAD_REQUEST)
    else:
        checking_period_days = int(checking_period_days)
    total_count = 0
    for project in projects:
        total_count += project.hit_count.hits_in_last(
            days=checking_period_days)

    return Response({'count': total_count, 'checking_period_days': checking_period_days})
