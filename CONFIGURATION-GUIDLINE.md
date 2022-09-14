# Nemo Configuration Guidline

There are different locations where we have configuration for Nemo.

1. [Nemo .env](.env): This configuration file indicates main configuration for the Nemo backend, database (Postgresql), mail server, external authentication provider, and other services defined in the `docker-compose.yml` at the root of Nemo directory.
1. [Nemo .env.ci](.env.ci): This configuration file is same as the Nemo env. This file is used during the continuous integration process on gitlab-ci.
1. [Nemo live development .env](live-development/.env): This configuration file is same as the Nemo env. This file is used during the development process.
1. [Nemo backend settings.py](backend/backend/settings.py): This is the Django configuration file.
1. [Nemo frontend AppConfig.js](frontend/public/AppConfig.js): This is the configuration file for the UI (react).
1. [Nemo nginx.conf](nginx/nginx.conf): This is the configuration file for the nginx.
