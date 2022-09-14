from django.apps import AppConfig
from apps.utils.dynamic_importer import scan


class DashboardConfig(AppConfig):
    name = 'apps.dashboard'

    def ready(self):
        import apps.dashboard.signals
        scan('apps.dashboard.evaluators')
        scan('apps.dashboard.data_collectors')
