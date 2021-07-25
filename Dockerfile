FROM python:3-slim

ADD . /archive-bot
WORKDIR /archive-bot
ENV WORKON_HOME=/var/tmp

RUN apt update && \
    apt install -y --no-install-recommends git gosu && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install pipenv && \
    pipenv install
