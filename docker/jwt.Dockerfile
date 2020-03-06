FROM python:3.7-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apk add --update --virtual .run-app \
        libpq \
    && rm -rf /var/cache/apk/*

COPY jwt-app/requirements.txt .

RUN apk add --update --virtual .build-app \
    gcc musl-dev postgresql-dev\
    && rm -rf /var/cache/apk/* \
    && pip install --upgrade pip==19.3.1 \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-app

COPY jwt-app/src .
