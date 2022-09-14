#!/usr/bin/env bash
set -euo pipefail
readonly CWD=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)

function main() {
  run_dependency_services
  run_frontend
  run_backend
}

function run_dependency_services() {
  cd "$CWD"
  docker-compose up -d
}

function run_frontend() {
  cd "$CWD/../frontend/"
  npm run start &
}

function run_backend() {
  cd "$CWD/../backend/"
  pipenv install --dev
  # shellcheck disable=SC2002
  # shellcheck disable=SC2046
  export $(cat "$CWD/.env" | xargs)
  export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
  pipenv run python manage.py collectstatic --no-input
  pipenv run python manage.py migrate
  pipenv run python manage.py runserver 0.0.0.0:8000
}

main "$@"
