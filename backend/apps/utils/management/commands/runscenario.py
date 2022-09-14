import importlib
import inspect
import traceback
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Runs a usage scenario.'
    requires_migrations_checks = True

    SETTINGS_NAME__DEFAULT_APP_FOR_SCENARIOS = 'DEFAULT_APP_FOR_SCENARIOS'
    ARG_NAME__APP_NAME = 'app-name'
    ARG_NAME__SCENARIO_NAME = 'scenario-name'
    ARG_NAME__ATOMIC = 'atomic'
    ARG_NAME__NONATOMIC = 'nonatomic'
    ATOMIC_EXECUTION_DEFAULT = True
    SCENARIOS_MODULE_NAME = 'scenarios'

    def add_arguments(self, parser):
        parser.add_argument(self.ARG_NAME__APP_NAME, nargs='?', type=str,
                            help="Name of the Django app from which the scenario is run.")
        parser.add_argument(self.ARG_NAME__SCENARIO_NAME, type=str,
                            help="Name of the scenario to run.")
        parser.add_argument(f'--{self.ARG_NAME__ATOMIC}', default=self.ATOMIC_EXECUTION_DEFAULT, action='store_true',
                            help="Runs the whole scenario in a single transaction.")
        parser.add_argument(f'--{self.ARG_NAME__NONATOMIC}', dest='atomic', action='store_false',
                            help="Runs the scenario without wrapping in a single transaction.")

    def handle(self, *args, **options):
        app_name = options.get(self.ARG_NAME__APP_NAME, None)
        scenario_name = options[self.ARG_NAME__SCENARIO_NAME]
        run_atomic = options[self.ARG_NAME__ATOMIC]
        if app_name is None:
            app_name = getattr(settings, self.SETTINGS_NAME__DEFAULT_APP_FOR_SCENARIOS, None)
            if app_name is None:
                raise CommandError("Django app name is not given as an argument, and "
                                    f"'{self.SETTINGS_NAME__DEFAULT_APP_FOR_SCENARIOS}' is not set in the settings either.")

        scenarios_module_path = f"{app_name}.{self.SCENARIOS_MODULE_NAME}"
        try:
            scenarios_module = importlib.import_module(scenarios_module_path)
        except ImportError as e:
            raise CommandError(f"Could not import module '{scenarios_module_path}': {e}")
        try:
            run_scenario = getattr(scenarios_module, scenario_name)
        except AttributeError:
            raise CommandError(f"Function '{scenario_name}()' is not defined in '{scenarios_module_path}'.")
        if not inspect.isfunction(run_scenario):
            raise CommandError(f"Attribute '{scenario_name}' defined in scenario '{scenarios_module_path}' is not a function!")

        self.stdout.write(self.style.MIGRATE_HEADING(f"Running scenario '{scenarios_module_path}'..."))
        try:
            if run_atomic:
                with transaction.atomic():
                    # This code executes inside a transaction.
                    run_scenario()
            else:
                run_scenario()
        except CommandError:
            raise
        except Exception as e:
            tb = traceback.format_exc()
            raise CommandError(f"Failed to run scenario '{scenario_name}' completely.\n{tb}")

        self.stdout.write(self.style.SUCCESS(f"Successfully ran scenario '{scenario_name}'."))
