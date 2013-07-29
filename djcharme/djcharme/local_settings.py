'''
Created on 14 May 2013

@author: mnagni
'''
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

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

'''
FUSEKI_URL = 'http://localhost:3333/privateds'
NODE_URI = 'http://proteus.badc.rl.ac.uk'

SPARQL_UPDATE = FUSEKI_URL + '/update'
SPARQL_QUERY = FUSEKI_URL + '/sparql'
SPARQL_DATA = FUSEKI_URL + '/data'

GRAPH_STORE_R = FUSEKI_URL + '/get'
GRAPH_STORE_RW = FUSEKI_URL + '/data'
'''
