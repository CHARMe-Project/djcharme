'''
BSD Licence
Copyright (c) 2014, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.
    * Neither the name of the Science & Technology Facilities Council (STFC)
        nor the names of its contributors may be used to endorse or promote
        products derived from this software without specific prior written
        permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Created on 9 Jan 2012

@author: Maurizio Nagni
'''


import logging
import mimetypes
from multiprocessing.process import Process

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.utils import DatabaseError
from django.http.response import HttpResponse
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

from djcharme import mm_render_to_response_error, LOAD_SAMPLE


def webusage(request):
    template = ('\nMETHOD:%s\nIP:%s\nREMOTE_HOST:%s\nPATH_INFO:%s\n' \
                'HTTP_USER_AGENT:%s\n')
    return template % (request.META.get('REQUEST_METHOD', 'Unknown'),
                       request.META.get('REMOTE_ADDR', 'Unknown'),
                       request.META.get('REMOTE_HOST', 'Unknown'),
                       request.META.get('PATH_INFO', 'Unknown'),
                       request.META.get('HTTP_USER_AGENT', 'Unknown'))


LOGGING = logging.getLogger(__name__)

USAGE_LOG = logging.getLogger('webusage')
USAGE_LOG.setLevel(logging.DEBUG)
# create console handler with a higher log level
HANDLER = logging.StreamHandler()
HANDLER.setLevel(logging.INFO)

# create file handler which logs even debug messages
# ch = logging.FileHandler('spam.log')
# ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
FORMATTER = logging.Formatter(fmt='%(name)s %(asctime)s \
%(message)s')
HANDLER.setFormatter(FORMATTER)
USAGE_LOG.addHandler(HANDLER)

# USAGE_LOG.basicConfig(format='%(name)s:%(levelname)s:%(message)s',
# level=logging.INFO,datefmt='%d/%m/%y %I:%M:%S')

if not mimetypes.inited:
    mimetypes.init()
    mimetypes.add_type('application/rdf+xml', '.rdf')
    mimetypes.add_type('text/turtle', '.ttl')
    mimetypes.add_type('application/ld+json', '.json-ld')


class CharmeMiddleware(object):

    __store = None
    __osEngine = None

    DEFAULT_OPTIONS_HDR_RESPONSE = {
        'Access-Control-Allow-Methods': 'GET, OPTIONS, POST, DELETE',
        'Access-Control-Allow-Headers': 'X-CSRFToken, X-Requested-With, ' \
            'x-requested-with, Content-Type, Content-Length, Authorization',
        'Access-Control-Max-Age': 10,
        'Content-Type': "text/plain"
    }

    @classmethod
    def __init_os_engine(self):
        from djcharme.opensearch.os_conf import setUp
        LOGGING.info("__init_os_engine - OpenSearch Engine created")
        CharmeMiddleware.__osEngine = setUp()

    @classmethod
    def __init_store(self):
        store = SPARQLUpdateStore(queryEndpoint=getattr(settings,
                                                        'SPARQL_QUERY'),
                                  update_endpoint=getattr(settings,
                                                          'SPARQL_UPDATE'),
                                 postAsEncoded=False)
        store.bind("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        store.bind("oa", "http://www.w3.org/ns/oa#")
        store.bind("chnode", getattr(settings, 'NODE_URI', 'http://localhost'))
        LOGGING.info("__init_store - Store created")
        CharmeMiddleware.__store = store

        # Creates a superuser if there is not any
        try:
            users = User.objects.all()
            if len(users) == 0:
                User.objects.create_superuser('admin', '', 'admin')
        except DatabaseError:
            LOGGING.error("__init_store - Cannot find or create an "
                          "application superuser")

    @classmethod
    def get_store(self, debug=False):
        if debug or CharmeMiddleware.__store is None:
            CharmeMiddleware.__init_store()
            if getattr(settings, LOAD_SAMPLE, False):
                LOGGING.info("get_store - LOAD_SAMPLE: %s", True)
                from djcharme.node.sample import load_sample
                proc = Process(target=load_sample)  # inits thread
                proc.start()  # starts thread
        return CharmeMiddleware.__store

    @classmethod
    def get_osengine(self, debug=False):
        if debug or CharmeMiddleware.__osEngine is None:
            CharmeMiddleware.__init_os_engine()
        return CharmeMiddleware.__osEngine

    def process_request(self, request):
        USAGE_LOG.info(webusage(request))
        if request.method == 'OPTIONS':
            return HttpResponse(status=200)

        if CharmeMiddleware.get_store() is None:
            try:
                self.__init_store()
            except AttributeError, ex:
                messages.add_message(request, messages.ERROR, ex)
                messages.add_message(request, messages.INFO,
                                     'Missing configuration')
                return mm_render_to_response_error(request, '503.html', 503)

        if CharmeMiddleware.get_osengine() is None:
            try:
                self.__init_os_engine()
            except Exception, ex:
                messages.add_message(request, messages.ERROR, ex)
                messages.add_message(request, messages.INFO,
                                     'Missing configuration. '
                                     'Cannot initialize OpenSearch Engine')
                return mm_render_to_response_error(request, '503.html', 503)

        self._validate_request(request)

    def process_response(self, request, response):
        response['Access-Control-Allow-Origin'
            ] = request.META.get('HTTP_ORIGIN', request.build_absolute_uri())

        response['Access-Control-Allow-Credentials'] = 'true'

        response['Access-Control-Expose-Headers'] = (
            'Location, Content-Type, Content-Length')

        if request.method == 'OPTIONS':
            # Take default settings from class variable if no settings
            if getattr(settings, 'OPTIONS_HDR_RESPONSE'):
                for key, value in settings.OPTIONS_HDR_RESPONSE.items():
                    response[key] = value
            else:
                for key, value in (
                    self.__class__.DEFAULT_OPTIONS_HDR_RESPONSE.items()):
                    response[key] = value

            return response
        else:
            return response

    def process_exception(self, request, exception):
        LOGGING.info("process_exception - %s", str(exception))

    def _get_user_roles(self, user):
        # user.roles = contact_role_server
        # return user
        pass

    def _is_authenticated(self, request):
        pass

    def _validate_request(self, request):
        user = self._is_authenticated(request)
        # Here should compare:
        # - the request method ('get/put/post/delete')
        # - the request resource ('URI')
        pass
