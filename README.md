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

## Deployment (Docker)

The recommended way to install the API and it's service dependancies is with docker, however the docker-compose config can also be used in development. I've found that this is best done if you're using a PC or Server.

**Doesn't play well with RPi!**

### System Dependancies

```bash
sudo apt update && sudo apt upgrade
sudo apt install libffi-dev libssl-dev python3-dev python3 python3-pip git
```

### Docker Compose Setup

#### Setting up docker

```bash
curl -fsSL test.docker.com -o get-docker.sh && sh get-docker.sh
sudo usermod -aG docker ${USER}
sudo systemctl enable docker
sudo reboot now  # or logout of the pi user account
```

#### Setting up docker-compose, the project and environment

```bash
pip3 install docker-compose
git clone https://github.com/hacklabza/iotserver.git
cd iotserver/
curl -#fLo- 'https://raw.githubusercontent.com/hyperupcall/autoenv/master/scripts/install.sh' | sh  # install autoenv - optional
cp .env.example .env  # update as required
mkdir -p docker/mqtt
cp mosquitto.conf.example docker/mqtt/mosquitto.conf
docker-compose -f docker-compose.yml up
```

## Deployment (Manual)

Recommend for 64bit/32bit rasbian installation, in my case a raspberrypi zero.

### System Dependancies

```bash
sudo apt update && sudo apt upgrade
sudo apt install -y --no-install-recommends git vim python3-pip python3-dev postgresql-client gdal-bin libgdal-dev libffi-dev openssl
```

### PostGIS Setup

```bash
sudo apt install -y --no-install-recommends postgresql
sudo chown postgres:postgres /var/lib/postgresql/13/main
sudo apt install postgresql-13-postgis-3-scripts
sudo su - postgres
createdb iotserver
psql -d iotserver
$postgres-# CREATE EXTENSION postgis;
```

### Memcached Setup

```bash
sudo apt install -y --no-install-recommends memcached
```

### MQTT Setup

```bash
sudo apt install -y --no-install-recommends mosquitto
```

Add the following lines to `/etc/mosquitto/mosquitto.conf` and restart the service

```bash
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
listener 1883
max_keepalive 0  # Remove if this causes startup issues
allow_anonymous true
```

### API Setup

```bash
git clone https://github.com/hacklabza/iotserver.git
cd iotserver/

curl -sSL https://install.python-poetry.org | python3 -
export CRYPTOGRAPHY_DONT_BUILD_RUST=1
poetry install

curl -#fLo- 'https://raw.githubusercontent.com/hyperupcall/autoenv/master/scripts/install.sh' | sh  # install autoenv - optional
cp .env.example .env  # update as required
cp manage.py ~/.local/bin/

poetry run manage.py migrate
poetry run manage.py collectstatic
poetry run manage.py createsuperuser

sudo cp systemd/iot.api.service /etc/systemd/system/iot.api.service
sudo cp systemd/iot.mqttsubscriber.service /etc/systemd/system/iot.mqttsubscriber.service

sudo systemctl start iot.api.service
sudo systemctl start iot.mqttsubscriber.service

sudo systemctl enable iot.api.service
sudo systemctl enable iot.mqttsubscriber.service
```
