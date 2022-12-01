FROM python

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client gdal-bin libgdal-dev
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

ENV PATH="${PATH}:/root/.local/bin"
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

COPY pyproject.toml /usr/src/app/pyproject.toml
COPY poetry.lock /usr/src/app/poetry.lock
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

EXPOSE 8000
