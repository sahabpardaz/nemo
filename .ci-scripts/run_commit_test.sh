#!/usr/bin/env bash
set -eu

cd ${CI_PROJECT_DIR}/nemo

./.ci-scripts/copy_database_init_script.sh

CONTAINER_NAME=test-nemo-with-report-${CI_JOB_ID}

set +e # Let the script continue in case of a test failure
docker-compose --env-file .env.ci --project-name ${CI_JOB_ID} \
run --name ${CONTAINER_NAME} web bash -c "./gitlab-ci-test-job-script.sh"
test_run_exit_code=$?
set -e

docker cp ${CONTAINER_NAME}:/nemo/backend/pylint-report.json backend/pylint-report.json
${CI_PROJECT_DIR}/prepare_pylint_codequality_report_for_gitlab.sh backend/pylint-report.json nemo/backend/
docker cp ${CONTAINER_NAME}:/nemo/backend/xunittest.xml backend/xunittest.xml
docker cp ${CONTAINER_NAME}:/nemo/backend/coverage.xml backend/coverage.xml

${CI_PROJECT_DIR}/.ci-cd-scripts/add_directory_prefix_to_coverage_report.sh \
--input backend/coverage.xml \
--directory-prefix nemo/backend/ \
--output backend/gitlab-coverage.xml

exit $test_run_exit_code
