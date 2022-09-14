#!/bin/bash

set -eo pipefail

directories_to_check=("apps" "backend")

cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export DJANGO_SETTINGS_MODULE="backend.settings"
pylint --load-plugins pylint_django --output-format=pylint_gitlab.GitlabCodeClimateReporter "${directories_to_check[@]}" | tee "pylint-report.json"
