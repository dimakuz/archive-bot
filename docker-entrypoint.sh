#!/bin/sh -xe

exec su-exec ${PUID:-0}:${PGID:-0} pipenv run python -m archive_bot.bot