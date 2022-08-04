FROM python

WORKDIR /usr/src/app

RUN apt-get install -y --no-install-recommends postgresql-client gdal-bin libgdal-dev

RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="${PATH}:/root/.cargo/bin"

RUN pip install -U pip \
  && pip install cleo tomlkit poetry.core requests cachecontrol cachy html5lib pkginfo virtualenv lockfile \
  && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

ENV PATH="${PATH}:/root/.poetry/bin"
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

COPY pyproject.toml /usr/src/app/pyproject.toml
COPY poetry.lock /usr/src/app/poetry.lock
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

RUN rustup self uninstall

COPY entrypoint.sh /bin/entrypoint.sh
COPY manage.py /bin/manage.py

EXPOSE 8000
