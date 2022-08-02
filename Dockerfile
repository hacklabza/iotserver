FROM python

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client gdal-bin libgdal-dev
RUN pip install -U pip \
  && pip install cleo tomlkit poetry.core requests cachecontrol cachy html5lib pkginfo virtualenv lockfile \
  && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

ENV PATH="${PATH}:/root/.poetry/bin"

COPY pyproject.toml /usr/src/app/pyproject.toml
COPY poetry.lock /usr/src/app/poetry.lock
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY entrypoint.sh /bin/entrypoint.sh
COPY manage.py /bin/manage.py

EXPOSE 8000
