#!/usr/bin/env bash

set -euo pipefail

readonly CWD=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
readonly PACKAGE_FILES_DIR="$CWD/nemo"
readonly NEMO_PROJECT_ROOT_DIR="$CWD/.."
readonly RELEASED_ENV_FILE_NEMO_VERSION=$($NEMO_PROJECT_ROOT_DIR/version.sh)
readonly RELEASED_ENV_FILE_DOCKER_REGISTRY=local

function main() {
    local DOCKER_REGISTRY="$1"
    local NEMO_VERSION_TO_PULL="$2"
    mkdir -p "$PACKAGE_FILES_DIR"
    add_docker_compose_file
    add_env_file "$DOCKER_REGISTRY"
    add_nginx_config
    add_postgres_init_script
    save_nemo_images "$DOCKER_REGISTRY" "$NEMO_VERSION_TO_PULL"
    add_installation_guide
    add_other_assets
    create_nemo_archive
}

function add_docker_compose_file() {
    cp "$NEMO_PROJECT_ROOT_DIR/docker-compose.yml" "$PACKAGE_FILES_DIR"
    yq 'del(.services.web.build), del(.services.frontend.build)' -i "$PACKAGE_FILES_DIR/docker-compose.yml"
}

function add_env_file() {
    local DOCKER_REGISTRY="$1"
    cd "$PACKAGE_FILES_DIR"
    cp "$NEMO_PROJECT_ROOT_DIR/.env" .
    sed -i "s/NEMO_VERSION=.*/NEMO_VERSION=$RELEASED_ENV_FILE_NEMO_VERSION/" .env
    sed -i "s/DOCKER_REGISTRY=.*/DOCKER_REGISTRY=$RELEASED_ENV_FILE_DOCKER_REGISTRY/" .env
    mkdir -p "$PACKAGE_FILES_DIR/custom-certificates/"
    sed -i "s/CUSTOM_CERTIFICATES_DIR=.*/CUSTOM_CERTIFICATES_DIR=.\/custom-certificates\//" .env
    sed -i "s/NEMO_OIDC_ROOT_URL=.*/NEMO_OIDC_ROOT_URL=/" .env
    sed -i "s/NEMO_OIDC_REALM=.*/NEMO_OIDC_REALM=/" .env
    sed -i "s/NEMO_OIDC_CLIENT=.*/NEMO_OIDC_CLIENT=/" .env
    sed -i "s/NEMO_OIDC_SECRET=.*/NEMO_OIDC_SECRET=/" .env
}

function add_nginx_config() {
    cd "$PACKAGE_FILES_DIR"
    mkdir ./nginx/
    cp "$NEMO_PROJECT_ROOT_DIR/nginx/nginx.conf" ./nginx/
}

function add_postgres_init_script() {
    cd "$PACKAGE_FILES_DIR"
    mkdir ./postgresql/
    cp "$NEMO_PROJECT_ROOT_DIR/postgresql/initialize-nemo-database.sh" ./postgresql/
}

function save_nemo_images() {
    local DOCKER_REGISTRY="$1"
    local NEMO_VERSION_TO_PULL="$2"
    local WEB_IMAGE=$DOCKER_REGISTRY/nemo-web:$NEMO_VERSION_TO_PULL
    local FRONTEND_IMAGE=$DOCKER_REGISTRY/nemo-frontend:$NEMO_VERSION_TO_PULL
    local WEB_IMAGE_TO_RELEASE=$RELEASED_ENV_FILE_DOCKER_REGISTRY/nemo-web:$RELEASED_ENV_FILE_NEMO_VERSION
    local FRONTEND_IMAGE_TO_RELEASE=$RELEASED_ENV_FILE_DOCKER_REGISTRY/nemo-frontend:$RELEASED_ENV_FILE_NEMO_VERSION
    cd "$NEMO_PROJECT_ROOT_DIR"
    echo "Pulling Nemo images ..."
    docker pull $WEB_IMAGE
    docker pull $FRONTEND_IMAGE
    docker tag $WEB_IMAGE $WEB_IMAGE_TO_RELEASE
    docker tag $FRONTEND_IMAGE $FRONTEND_IMAGE_TO_RELEASE
    cd "$PACKAGE_FILES_DIR"
    echo "Saving web-image.tar ..."
    docker save $WEB_IMAGE_TO_RELEASE -o web-image.tar
    echo "Saving frontend-image.tar ..."
    docker save $FRONTEND_IMAGE_TO_RELEASE -o frontend-image.tar
}

function add_installation_guide() {
    cp "$CWD/INSTALL.md" "$PACKAGE_FILES_DIR"
}

function add_other_assets() {
    cp -r "$CWD/other-assets/"* "$PACKAGE_FILES_DIR/"
    chmod +x "$PACKAGE_FILES_DIR/load-images.sh"
}

function create_nemo_archive() {
    echo "Creating nemo.tar.gz ..."
    cd "$CWD"
    tar czf nemo.tar.gz nemo/
}

main "$@"
