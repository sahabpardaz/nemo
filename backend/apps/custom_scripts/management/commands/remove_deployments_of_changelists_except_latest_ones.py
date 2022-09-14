from datetime import datetime
import pytz
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.custom_scripts.deployment_pruning import remove_deployments_of_changelists_except_latest_ones


class Command(BaseCommand):
    help = (
        'Keeps latest deployment reports With pass status priority '
        'of changelists in specific time period and deletes the others'
    )

    def add_arguments(self, parser):
        parser.add_argument('project_id', type=int, help='ID of project')
        parser.add_argument('period_start_timestamp', nargs='?', type=int, default=None, help='Start timestamp of period')
        parser.add_argument('period_end_timestamp', nargs='?', type=int, default=None, help='End timestamp of period')

    def handle(self, *args, **options):
        time_zone = pytz.timezone(settings.TIME_ZONE)
        period_start_time = None
        if options.get('period_start_timestamp'):
            datetime.fromtimestamp(options.get('period_start_timestamp'), time_zone)
        period_end_time = None
        if options.get('period_end_timestamp'):
            datetime.fromtimestamp(options.get('period_end_timestamp'), time_zone)

        remove_deployments_of_changelists_except_latest_ones(
            project_id=options.get('project_id'),
            period_start=period_start_time,
            period_end=period_end_time,
        )
        self.stdout.write(self.style.SUCCESS(f"Operation completed successfully."))
