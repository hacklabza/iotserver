FROM python:3.10-bookworm

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client gdal-bin libgdal-dev
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="${PATH}:/root/.local/bin"

COPY . /usr/src/app

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

EXPOSE 8000
