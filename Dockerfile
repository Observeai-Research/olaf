FROM --platform=linux/amd64 python:3.8-bullseye
RUN apt-get update
RUN apt-get -y install nginx supervisor gettext-base
RUN pip install poetry

WORKDIR /olaf
COPY poetry.lock pyproject.toml /olaf/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

COPY ./src ./src
COPY nginx.htpassd.template supervisord.conf ./
COPY nginx.conf.template /etc/nginx/nginx.conf
COPY nginx.htpassd.template /etc/nginx/nginx.htpassd

ENV ENVIRONMENT=''
ENV ENCRYPTION_KEY=''

HEALTHCHECK --start-period=150s CMD curl --fail http://localhost:8000/health || exit 1
CMD supervisord -c supervisord.conf