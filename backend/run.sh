#!/bin/bash

set -euo pipefail

# Install custom certificates if any
# If any third party service (like gitlab, sonar, etc.) that Nemo interacts with it uses custom certificates,
# you should add the files in "custom-runtime-certificates" dir next to docker-compose.yml
update-ca-certificates

/wait

supervisord -c backend/configs/celery-supervisord.conf
supervisord -c backend/configs/celery-beat-supervisord.conf

python manage.py migrate

gunicorn --bind 0.0.0.0:8000 --workers=9 \
      --worker-class=gevent --worker-connections=1000 \
      --access-logfile /var/log/nemo/gunicorn/access.log \
      --error-logfile /var/log/nemo/gunicorn/error.log \
      backend.wsgi:application
