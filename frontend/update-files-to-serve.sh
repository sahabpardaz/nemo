#!/usr/bin/env bash

set -e

if [ -z "$API_URL" ]; then
    echo >&2 "API_URL env var is not defined!"
    exit 1
fi

rsync -r /local/frontend/ /nemo/frontend/ --delete
echo "Frontend files updated successfully!"

readonly app_config_file="/nemo/frontend/AppConfig.js"

function change_config_value() {
    local KEY=$1
    local VALUE=$2
    sed -r -i "s/${KEY}:.+\,/${KEY}: ${VALUE}\,/g" "${app_config_file}"
}

url_regex='(https?)://[-A-Za-z0-9\+&@#/%?=~_|!:,.;]*[-A-Za-z0-9\+&@#/%=~_|]'
if [[ ! $API_URL =~ $url_regex ]]
then
    echo "API_URL environment variable is not valid. (Example: http://localhost/)"
    exit 1
fi

# Read API_URL from environment and place it in AppConfig
change_config_value "API_URL" "'${API_URL//\//\\/}'"
# Set copyright year in AppConfig
change_config_value "COPYRIGHT_YEAR" "$(date +'%Y')"
# Set sentry DSN to report
change_config_value "SENTRY_DSN" "'${SENTRY_DSN//\//\\/}'"
# Set senty environment name to distinguish reports between running instances of app
readonly domain_name=$(echo "${API_URL}" | awk -F/ '{print $3}')
change_config_value "SENTRY_ENVIRONMENT" "'${domain_name}'"
# Set Nemo version
change_config_value "NEMO_VERSION" "'$NEMO_VERSION'"
echo "AppConfig updated successfully!"
echo "$(cat ${app_config_file})"
