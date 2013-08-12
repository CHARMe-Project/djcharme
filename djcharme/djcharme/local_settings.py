'''
Created on 14 May 2013

@author: mnagni
'''

#############
# DATABASES #
#############
'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '<DB_PATH>',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
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
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
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

def _format_fuseki_url(service):
    return 'http://%s:%s/%s/%s' % (FUSEKI_URL, FUSEKI_PORT, NODE_ROOT_URL, service)

FUSEKI_URL = 'localhost'
FUSEKI_PORT = '3333'
NODE_URI = 'http://proteus.badc.rl.ac.uk:8000'
NODE_ROOT_URL = 'privateds'


SPARQL_UPDATE = _format_fuseki_url('update')
SPARQL_QUERY = _format_fuseki_url('sparql')
SPARQL_DATA = _format_fuseki_url('data')

GRAPH_STORE_RW_PATH = '/%s/%s' % (NODE_ROOT_URL, 'data')
GRAPH_STORE_DATA = FUSEKI_URL + NODE_ROOT_URL + '/data'
GRAPH_STORE_R = FUSEKI_URL + NODE_ROOT_URL +'/get'
'''
