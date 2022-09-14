FROM python:3.8.12

ARG PIP_REPOSITORY_INDEX_URL
ARG ALBORZ_RAW_REPOSITORY
ARG APT_PROXY

# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1

# Script checks database is fully up and ready
# Pass variable WAIT_HOSTS like this: WAIT_HOSTS=database:5432,otherservice:1234
ADD "$ALBORZ_RAW_REPOSITORY/nemo/wait-2.7.3" /wait
RUN chmod +x /wait

# Set REQUESTS_CA_BUNDLE to use system wide certificates that installed with update-ca-certificate command
ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

RUN echo "[global]" > /etc/pip.conf && \
    echo "index-url = $PIP_REPOSITORY_INDEX_URL" >> /etc/pip.conf

RUN echo "Acquire::http::Proxy \"${APT_PROXY}\";" > /etc/apt/apt.conf.d/aptproxy
WORKDIR /tmp/
COPY ./requirements-apt.txt .
RUN apt-get update && cat ./requirements-apt.txt | xargs apt-get install -y

RUN pip install pip==21.1.2 pipenv==2022.1.8
COPY ./Pipfile ./Pipfile.lock ./
RUN pipenv install --ignore-pipfile --dev --deploy --system

WORKDIR /nemo/backend/
COPY . ./
RUN NEMO_DJANGO_SECRET_KEY=dummy python manage.py collectstatic --no-input
RUN chmod +x run.sh