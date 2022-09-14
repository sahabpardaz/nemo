from rest_framework_extensions.settings import extensions_api_settings


PARENT_LOOKUP_PROJECT = 'project_id'

PARENT_LOOKUP_ENVIRONMENT = 'environment_id'

PROJECT_ID_URL_PARAMETER = \
            extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX + PARENT_LOOKUP_PROJECT

ENVIRONMENT_ID_URL_PARAMETER = \
            extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX + PARENT_LOOKUP_ENVIRONMENT

DEPLOYMENT_NOT_ENOUGH = 'Deployments not enough to calculate.'

KEY_CHANGE_FAILURE_RATE = "change_failure_rate"

KEY_TIME_TO_RESTORE = "time_to_restore"

KEY_LEAD_TIME = "lead_time"

KEY_DEPLOYMENT_FREQUENCY = "deployment_frequency"

DEFAULT_CHECKING_PERIOD_DAYS = 62  # 2 months

DEFAULT_PERIOD_IN_DAYS = 186  # 6 months

MAX_PERIOD_IN_DAYS = 186  # 6 months
