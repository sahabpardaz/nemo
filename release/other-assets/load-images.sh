#!/usr/bin/env bash

# This script loads the Nemo docker images' tar files.

set -euo pipefail
readonly CWD=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)

docker load -i "$CWD/web-image.tar"
docker load -i "$CWD/frontend-image.tar"
