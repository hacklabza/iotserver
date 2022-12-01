#!/usr/bin/env bash

./manage.py migrate --noinput
./manage.py collectstatic --noinput
gunicorn iotserver.wsgi:application -w 2 -b :8000 --reload && ./manage.py mqtt
