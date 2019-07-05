#!/usr/bin/env python
# -*-encoding:UTF-8-*-
from myutils.shortcuts import get_env

#
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': get_env("POSTGRES_HOST", "icqbpmssoj-postgres"),
        'PORT': get_env("POSTGRES_HOST", "5432"),
        'NAME': get_env("POSTGRES_DB"),
        'USER': get_env("POSTGRES_USER"),
        'PASSWORD': get_env("POSTGRES_PASSWORD")
    }
}

#
REDIS_CONF = {
    "host": get_env("REDIS_HOST", "icqbpmssoj-redis"),
    "port": get_env("REDIS_PORT", "6379")
}

# if DEBUG is False, you also need to properly set the ALLOWED_HOSTS setting.
# Failing to do so will result in all requests being returned as “Bad Request (400)”.
DEBUG = False

#
ALLOWED_HOSTS = ['*']

DATA_DIR = "/data"
