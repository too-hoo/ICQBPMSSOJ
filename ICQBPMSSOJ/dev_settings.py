#!/usr/bin/env python
# -*-encoding:UTF-8-*-
import os

# os.path.abspath(__file__) will return the absolute path of .py file（full path）
# os.path.dirname(__file__) will return the file dir of .py
# basedir is the root dir:ICQBPMSSOJ
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# postgresql:default port 5432, use 5435 to avoid being the same
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': '127.0.0.1',
        'PORT': 5435,
        'NAME': "icqbpmssoj",
        'USER': "icqbpmssoj",
        'PASSWORD': 'icqbpmssoj'
    }
}

# redis:default port6379, use 6380 to avoid being the same
REDIS_CONF = {
    "host": "127.0.0.1",
    "port": "6380"
}

# When DEBUG is True and ALLOWED_HOSTS is empty, the host is validated against ['localhost', '127.0.0.1', '[::1]'].
DEBUG = True

# A list of strings representing the host/domain names that this Django site can serve.
# A value of '*' will match anything; in this case you are responsible to provide your own
# validation of the Host header (perhaps in a middleware; if so this middleware must
# be listed first in MIDDLEWARE)
ALLOWED_HOSTS = ["*"]

# 注意这个路径是对应的开发环境的，就是在Pycharm里面的工程目录
# this path is dev path ,root dir is ICQBPMSSOJ
DATA_DIR = f"{BASE_DIR}/data"
