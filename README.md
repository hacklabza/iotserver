# IoT Server

Simple IoT Server, Configuration Tool & Dashboard

## Requirements

- Python 3.10+
- Git
- Mosquitto
- PostgreSQL
- PostGIS
- gdal

For more information on install spatialite see: https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/spatialite/

## Installation

```bash
$ git clone git@github.com:hacklabza/iotserver.git
$ cd iotserver/
pyenv local 3.10.*
poetry install
```

If you have issues with sqlite extensions, try this when install python via pyenv:

```bash
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" \
LDFLAGS="-L/usr/local/opt/sqlite/lib" \
CPPFLAGS="-I/usr/local/opt/sqlite/include" \
pyenv install 3.10.*
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
