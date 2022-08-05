# IoT Server (v0.9.0)

Simple IoT Server, Configuration Tool & Dashboard

## Requirements

- Python 3.9+
- Git
- Mosquitto
- PostgreSQL
- PostGIS
- gdal

## Installation

```bash
$ git clone https://github.com/hacklabza/iotserver.git
$ cd iotserver/
pyenv local 3.10.*
poetry Installation
```

### Run the server to test your installation

```bash
poetry run ./manage.py migrate
$ poetry run ./manage.py runserver
```

## Testing

```bash
poetry run pytest .
```

## Getting Started

To create a super user which you can use to populate your devices and users, execute the following command in your terminal and follow the prompts.

```bash
./manage.py createsuperuser
```

## Deployment

The recommended way to install the API and it's service dependancies is with docker, however the docker-compose config can also be used in development.

In my case I've deployed the API and services to a raspberrypi zero and was unable to get docker-compose to work. These are the steps I took to install it directly to the zero.

### System Dependancies

```bash
sudo apt update
sudo apt install -y --no-install-recommends git vim python3-pip postgresql-client gdal-bin libgdal-dev openssl
```

### PostGIS Setup

```bash
sudo apt install -y --no-install-recommends postgresql postgis
sudo su - postgres
$postgres-# CREATE EXTENSION postgis;
```

### API Setup

```bash
git clone https://github.com/hacklabza/iotserver.git
cd iotserver/

curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
export CRYPTOGRAPHY_DONT_BUILD_RUST=1
poetry install

./manage.py migrate --noinput
./manage.py collectstatic --noinput
./manage.py createsuperuser

poetry run gunicorn iotserver.wsgi:application -w 4 -b :8000 --reload
poetry run manage.py mqtt
```
