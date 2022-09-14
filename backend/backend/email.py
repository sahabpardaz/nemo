import os
from distutils.util import strtobool
from celery.schedules import crontab


EMAIL_ENABLED = strtobool(os.environ.get('EMAIL_ENABLED', 'False'))

if EMAIL_ENABLED:
    EMAIL_BACKEND = 'mailer.backend.DbBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_USE_TLS = bool(strtobool(os.environ.get('EMAIL_USE_TLS', 'True')))
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

    EMAIL_SENDER_DISPLAY_NAME = os.environ.get('EMAIL_SENDER_DISPLAY_NAME')
    if EMAIL_SENDER_DISPLAY_NAME:
        EMAIL_SENDER = f'{EMAIL_SENDER_DISPLAY_NAME} <{EMAIL_HOST_USER}>'
    else:
        EMAIL_SENDER = EMAIL_HOST_USER

SEND_QUEUED_EMAILS_INTERVAL = crontab()

RETRY_DEFERRED_EMAILS_INTERVAL = crontab(minute=0)
