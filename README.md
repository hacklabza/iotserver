# IoT Server

Simple IoT Server, Configuration Tool & Dashboard

[![Build Status](https://app.travis-ci.com/hacklabza/iotserver.svg?branch=develop)](https://app.travis-ci.com/hacklabza/iotserver)

## Requirements

 - Python 3.9+
 - Git
 - Mosquitto
 - SQLite
 - spatialite-tools
 - gdal

For more information on install spatialite see: https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/spatialite/

## Installation

```bash
$ git clone git@github.com:hacklabza/iotserver.git
$ cd iotserver/

# Create a virtualenv or use pyenv
$ python3 -m venv ve
$ . ve/bin/activate

# Install the requirements
$ pip install -r requirements.txt

# Run the server to test your installation
$ ./manage.py migrate
$ ./manage.py runserver
```

## Testing

```bash
$ make test
```

## Getting Started

To create a super user which you can use to populate your devices and users, execute the following command in your terminal and follow the prompts.

```bash
./manage.py createsuperuser
```
