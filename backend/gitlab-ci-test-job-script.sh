#!/bin/bash
# Gitlab test job

set -euo pipefail

/wait &
wpid=$!
./run-pylint.sh
wait "${wpid}"
python manage.py test
