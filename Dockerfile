FROM python

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client gdal-bin libgdal-dev
RUN curl --proto '=https' --tlsv1.2 https://sh.rustup.rs > rustup.sh && sh rustup.sh -y
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="${PATH}:/root/.local/bin"

COPY pyproject.toml /usr/src/app/pyproject.toml
COPY poetry.lock /usr/src/app/poetry.lock
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

EXPOSE 8000
