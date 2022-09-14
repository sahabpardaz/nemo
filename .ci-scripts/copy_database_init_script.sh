#!/usr/bin/env bash

# Since the database init script can't be mounted when running on CI, the mount
# of that script is disabled in this situation and instead, the current script
# copies the init script to the appropriate location in the database service
# container, before the service comes up.
# To see why mounting doesn't work see: https://stackoverflow.com/a/55481515/1655335

set -eu

cd "${CI_PROJECT_DIR}/nemo/"
docker-compose --env-file .env.ci --project-name ${CI_JOB_ID} create database
database_service_name=${CI_JOB_ID}_database_1 # Docker compose convention.
docker cp ./postgresql/initialize-nemo-database.sh $database_service_name:/docker-entrypoint-initdb.d/
