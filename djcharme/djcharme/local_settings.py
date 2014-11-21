'''
Created on 14 May 2013

@author: mnagni
'''
from os import path


THIS_DIR = path.dirname(__file__)

#############
# DATABASES #
#############

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Or path to database file if using sqlite3.
        'NAME': path.join(THIS_DIR, 'sqlite.db'),
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        # Empty for localhost through domain sockets or '127.0.0.1' for
        # localhost through TCP.
        'HOST': '',
        # Set to empty string for default.
        'PORT': '',
    }
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format':
            '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'djcharme': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}

# site settings
SITE_PREFIX = ""

LOAD_SAMPLE = False

# proxy settings
# HTTP_PROXY = 'proxy.domain'
# HTTP_PROXY_PORT = 8080

STATIC_URL = SITE_PREFIX + "/static/"

_format_sparql_url = lambda service: 'http://%s:%s/%s/%s' % (SPARQL_HOST_NAME,
                                                             SPARQL_PORT,
                                                             SPARQL_DATASET,
                                                             service)

SPARQL_HOST_NAME = 'localhost'
SPARQL_PORT = '3333'
SPARQL_DATASET = 'privateds'

SPARQL_UPDATE = _format_sparql_url('update')
SPARQL_QUERY = _format_sparql_url('sparql')
SPARQL_DATA = _format_sparql_url('data')

GRAPH_STORE_RW_PATH = '/%s/%s' % (SPARQL_DATASET, 'data')

NODE_URI = 'http://localhost:8000'

EMAIL_HOST = "localhost"
EMAIL_PORT = 25
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = ""
