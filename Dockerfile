FROM python:3-alpine

ADD . /archive-bot
WORKDIR /archive-bot
ENV WORKON_HOME=/var/tmp

RUN apk add su-exec qpdf libxml2 libxslt && \
    pip3 install pipenv && \
    apk add --virtual .build-deps gcc g++ libc-dev libxml2-dev libxslt-dev qpdf-dev && \
    pipenv install && \
    apk del .build-deps && \
    rm -rf /var/lib/apt/lists/*

ENV PUID=0
ENV PGID=0
ENTRYPOINT [ "/archive-bot/docker-entrypoint.sh" ]