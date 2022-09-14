#!/usr/bin/env bash

set -euo pipefail

readonly VERSION="0.1"
readonly CWD=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
readonly ROOT_DIR="$CWD/../.."
readonly NEW_MIGRATIONS_DIR_NAME="new-migrations"
readonly APPS=(dashboard devops_metrics)

function main() {
  if [ $# -ge 1 ]; then
    print_help
    exit 0
  fi

  check_new_migration_files_exist
  check_current_migrations_are_up_to_date_with_db
  unregister_current_migrations
  remove_current_migration_files
  copy_new_migration_files
  register_new_migrations
}

function print_help() {
  echo "Migrations Refresh Tool v${VERSION}"
  echo "This tool replaces an equivalent migration file with the old ones."
  echo "Just put the new migrations for 'dashboard' and 'devops_metrics' apps in './${NEW_MIGRATIONS_DIR_NAME}/[app name]/' dir."
  echo "This tool needs to be run inside the running Nemo web container to update the state of migrations in database."
  echo "Note that currently, for both apps the new migrations should exist, for this tool to work correctly."
}

function check_new_migration_files_exist() {
  echo "### Checking new migration files exist ..."
  cd "$CWD"
  local missing_migration_exists=false
  for app in "${APPS[@]}"; do
    local app_new_migrations_dir="./${NEW_MIGRATIONS_DIR_NAME}/${app}"
    if [ ! -d "$app_new_migrations_dir" ] || [ -z "$(ls -A "$app_new_migrations_dir")" ]; then
      echo "Error: Add new migrations for app '$app'"
      missing_migration_exists=true
    fi
  done
  if $missing_migration_exists; then
    exit 1
  fi
}

function check_current_migrations_are_up_to_date_with_db() {
  echo "### Checking current migrations are up to date with database ..."
  cd "$ROOT_DIR"
  python manage.py makemigrations --check --dry-run
}

function unregister_current_migrations() {
  echo "### Unregistering current migrations ..."
  cd "$ROOT_DIR"
  for app in "${APPS[@]}"; do
    python manage.py migrate --fake "$app" zero
  done
}

function remove_current_migration_files() {
  echo "### Removing current migration files ..."
  for app in "${APPS[@]}"; do
    rm "$ROOT_DIR/apps/$app/migrations/"*
    touch "$ROOT_DIR/apps/$app/migrations/__init__.py"
  done
}

function copy_new_migration_files() {
  echo "### Copying new migration files ..."
  for app in "${APPS[@]}"; do
    cp "$CWD/$NEW_MIGRATIONS_DIR_NAME/${app}/"* "$ROOT_DIR/apps/$app/migrations/"
  done
}

function register_new_migrations() {
  echo "### Registering new migration files ..."
  cd "$ROOT_DIR"
  python manage.py migrate --fake-initial
}

main "$@"
