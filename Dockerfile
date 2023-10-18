FROM 3.10-bullseye

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client gdal-bin libgdal-dev
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="${PATH}:/root/.local/bin"

COPY pyproject.toml /usr/src/app/pyproject.toml
COPY poetry.lock /usr/src/app/poetry.lock
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY entrypoint.sh /bin/entrypoint.sh
COPY manage.py /bin/manage.py

RUN chmod +x /bin/entrypoint.sh
RUN chmod +x /bin/manage.py

EXPOSE 8000
