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
