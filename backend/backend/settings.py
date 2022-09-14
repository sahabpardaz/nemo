import os
import logging
import warnings
from urllib.parse import urlparse
from seal.exceptions import UnsealedAttributeAccess
import sentry_sdk
from celery.schedules import crontab
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from .email import *  # pylint: disable=wildcard-import


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get('NEMO_DJANGO_SECRET_KEY')

DEBUG = os.environ.get('NEMO_DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [os.environ.get('NEMO_DJANGO_DEPLOY_HOST', '*')]

CORS_ORIGIN_ALLOW_ALL = os.environ.get(
    'NEMO_DJANGO_CORS_ALLOW_ALL', 'False') == 'True'

API_URL = 'http://nginx'

CORS_ORIGIN_WHITELIST = (
    'http://localhost',
)

FRONTEND_HOST = os.environ.get('NEMO_BASE_URL')

if FRONTEND_HOST is not None:
    CORS_ORIGIN_WHITELIST += (FRONTEND_HOST,)

DEFAULT_APP_FOR_SCENARIOS = 'apps.dashboard'

PROJECT_APPS = [
    'apps.utils',
    'apps.changelist_reporter',
    'apps.devops_metrics',
    'apps.dashboard',
    'apps.custom_scripts',
    'apps.oidc_authentication',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'mozilla_django_oidc',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'ordered_model',
    'nested_inline',
    'corsheaders',
    'drf_yasg',
    'django_celery_beat',
    'django_extensions',
    'django_nose',
    'rangefilter',
    'rest_condition',
    'guardian',
    'hitcount',
    'mailer',
    'request_profiler',
    'django_prometheus',
] + PROJECT_APPS

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # Prometheus middlewares should be the first and last ones.
    # For more details, See: https://github.com/korfuri/django-prometheus#quickstart
    'request_profiler.middleware.ProfilingMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',  # This should be last
]

ROOT_URLCONF = 'backend.urls'

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': os.environ.get('NEMO_DB_NAME'),
        'USER': os.environ.get('NEMO_DB_USER'),
        'PASSWORD': os.environ.get('NEMO_DB_PASSWORD'),
        'HOST': os.environ.get('NEMO_DB_HOST'),
        'PORT': 5432,
        'TEST': {
            'NAME': 'test_nemo',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CACHE_NAME_DEFAULT = 'default'
CACHE_NAME_FILE_BASED = 'file-based'

CACHES = {
    CACHE_NAME_DEFAULT: {
        'BACKEND': 'django_prometheus.cache.backends.locmem.LocMemCache'
    },
    CACHE_NAME_FILE_BASED: {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/opt/nemo/file-based-cache/',
        'TIMEOUT': 24 * 60 * 60,
    },
}

AUTHENTICATION_DEFAULT_RETURN_URL = "/"

AUTHENTICATION_BACKENDS = [
    'apps.oidc_authentication.auth_backend.AuthBackend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'mozilla_django_oidc.contrib.drf.OIDCAuthentication',
        "rest_framework.authentication.SessionAuthentication",
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        "rest_framework.permissions.IsAuthenticated",
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'EXCEPTION_HANDLER': 'apps.utils.exception_utils.sentry_exception_handler',
}

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

USE_X_FORWARDED_HOST = True
FORCE_SCRIPT_NAME = '/api'
STATIC_SUFFIX = '/static/'
STATIC_URL = FORCE_SCRIPT_NAME + STATIC_SUFFIX

LOG_ROOT = os.environ.get('DJANGO_LOG_ROOT', '/var/log/nemo/django/')

logging.captureWarnings(True)

warnings.filterwarnings('error', category=UnsealedAttributeAccess)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} - {pathname} [{funcName}] - {levelname} - {message} - {stack_info}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} - {levelname} - {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'debug_file': {
            'level': 'DEBUG',
            'class': 'backend.logging.MakeFileHandler',
            'filename': LOG_ROOT + 'debug.log',
            'filters': ['require_debug_true'],
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'backend.logging.MakeFileHandler',
            'filename': LOG_ROOT + 'error.log',
            'formatter': 'verbose',
        },
        'info_file': {
            'level': 'INFO',
            'class': 'backend.logging.MakeFileHandler',
            'filename': LOG_ROOT + 'info.log',
            'formatter': 'simple',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {
            'handlers': ['error_file', 'info_file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps.custom_scripts': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': True,
}

CELERY_BROKER_URL = 'amqp://message_broker:5672//'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

AUTO_EVALUATION_INTERVAL_IN_MINUTES = 15
AUTO_DATA_COLLECTION_INTERVAL_IN_MINUTES = 15
assert AUTO_EVALUATION_INTERVAL_IN_MINUTES == AUTO_DATA_COLLECTION_INTERVAL_IN_MINUTES, \
    "Intervals of 'evaluation' and 'data collection' tasks are not equal anymore. \
        Make sure the crontabs don't overlap (for performance's sake) and update this assertion accordingly."
AUTO_EVALUATION_INTERVAL = crontab(minute=f'{AUTO_DATA_COLLECTION_INTERVAL_IN_MINUTES//2}-59/{AUTO_EVALUATION_INTERVAL_IN_MINUTES}')
AUTO_DATA_COLLECTION_INTERVAL = crontab(minute=f'*/{AUTO_DATA_COLLECTION_INTERVAL_IN_MINUTES}')
PROJECTS_MATURITY_STATE_OBSERVE_INTERVAL = crontab(minute=0)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--with-coverage',
    '--cover-xml',
    f'--cover-package={",".join(PROJECT_APPS)}',
    '--with-xunit',
    '--xunit-file=xunittest.xml',
]

PROJECT_TOKEN_HEADER = "NEMO-PROJECT-TOKEN"

IPWARE_META_PRECEDENCE_ORDER = (
    'HTTP_X_FORWARDED_FOR',
    'X_FORWARDED_FOR',
)

SENTRY_REPORTER_ENABLED = os.environ.get('SENTRY_REPORTER_ENABLED', 'False') == 'True'

if SENTRY_REPORTER_ENABLED:
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    assert (
        SENTRY_DSN
    ), "Please define SENTRY_DSN environment variable if you enabled Sentry reporter"
    hostname = urlparse(os.environ.get('NEMO_BASE_URL')).netloc
    sentry_sdk.init(
        environment=hostname,
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        send_default_pii=True,
    )

HITCOUNT_KEEP_HIT_ACTIVE = {'hours': 24}
NEMO_HITCOUNT_DEFAULT_CHECKING_PERIOD_DAYS = 7

MAX_PROCESS_TIME_OF_REQUESTS_TO_ALERT_IN_SECONDS = 2.0

PROMETHEUS_EXPORT_MIGRATIONS = False

DORY_API_URL = "dory.ir"

MEDIA_ROOT = "media"

DORY_EVALUATION_RESULTS_SUBDIR = 'dory-evaluation-results'

FILES_GARABAGE_COLLECTION_PERIOD = crontab(minute='0', hour='0', day_of_week='0')
FILES_RETENTION_DAYS = 31

DORY_EVALUATION_MATURITY_ITEM_RESULTS_FILES_GARABAGE_COLLECTION_PERIOD = FILES_GARABAGE_COLLECTION_PERIOD
DORY_EVALUATION_MATURITY_ITEM_RESULTS_FILES_RETENTION_DAYS = FILES_RETENTION_DAYS

OIDC_ROOT_URL = os.environ.get('NEMO_OIDC_ROOT_URL')
OIDC_REALM = os.environ.get('NEMO_OIDC_REALM')
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_OP_JWKS_ENDPOINT = f'{OIDC_ROOT_URL}/realms/{OIDC_REALM}/protocol/openid-connect/certs'
OIDC_RP_CLIENT_ID = os.environ.get('NEMO_OIDC_CLIENT')
OIDC_RP_CLIENT_SECRET = os.environ.get('NEMO_OIDC_SECRET')
OIDC_OP_AUTHORIZATION_ENDPOINT = f'{OIDC_ROOT_URL}/realms/{OIDC_REALM}/protocol/openid-connect/auth'
OIDC_OP_TOKEN_ENDPOINT = f'{OIDC_ROOT_URL}/realms/{OIDC_REALM}/protocol/openid-connect/token'
OIDC_OP_USER_ENDPOINT = f'{OIDC_ROOT_URL}/realms/{OIDC_REALM}/protocol/openid-connect/userinfo'
OIDC_DRF_AUTH_BACKEND = 'mozilla_django_oidc.auth.OIDCAuthenticationBackend'
