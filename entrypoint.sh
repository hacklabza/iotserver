#!/usr/bin/env bash

./manage.py migrate --noinput
./manage.py collectstatic --noinput
./manage.py mqtt &
gunicorn iotserver.wsgi:application -w 2 -b :8000 --reload
