'''
BSD Licence
Copyright (c) 2012, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, 
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the documentation
        and/or other materials provided with the distribution.
    * Neither the name of the Science & Technology Facilities Council (STFC) 
        nor the names of its contributors may be used to endorse or promote 
        products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, 
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Created on 9 Jan 2012

@author: Maurizio Nagni
'''


import logging
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from django.conf import settings
from django.contrib import messages
from djcharme import mm_render_to_response_error
from django.contrib.auth.models import User
from django.db.utils import DatabaseError
from django.http.response import HttpResponse

formatter = logging.Formatter(fmt='%(name)s %(levelname)s %(asctime)s %(module)s %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)
#Temporary solution!!!
loggers = ('djcharme',)
for log_name in loggers:
    log = logging.getLogger(log_name)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

LOGGING = logging.getLogger(__name__)

import mimetypes
if not mimetypes.inited:
    mimetypes.init()
    mimetypes.add_type('application/rdf+xml', '.rdf')
    mimetypes.add_type('text/turtle', '.ttl')
    mimetypes.add_type('application/ld+json', '.json-ld')

class CharmeMiddleware(object):
      
    __store = None  
    __osEngine = None

    @classmethod   
    def __initOsEngine(self):
        from djcharme.opensearch.os_conf import setUp
        LOGGING.info("OpenSearch Engine created")
        CharmeMiddleware.__osEngine =setUp()
         

    @classmethod   
    def __initStore(self): 
        store = SPARQLUpdateStore(queryEndpoint = getattr(settings,
                                                              'SPARQL_QUERY'),
                                update_endpoint = getattr(settings,
                                                          'SPARQL_UPDATE'), 
                                postAsEncoded=False)
        store.bind("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        store.bind("oa", "http://www.w3.org/ns/oa#")
        store.bind("chnode", getattr(settings, 'NODE_URI', 'http://localhost'))
        LOGGING.info("Store created")
        CharmeMiddleware.__store = store
        
        #Creates a superuser if there is not any
        try:
            users = User.objects.all()
            if len(users) == 0:
                User.objects.create_superuser('admin', '', 'admin')
        except DatabaseError:
            LOGGING.error("Cannot find or create an application superuser")         
      
      
    @classmethod
    def get_store(self, debug = False):        
        if debug or CharmeMiddleware.__store is None:
            CharmeMiddleware.__initStore()
        return CharmeMiddleware.__store
      
    @classmethod
    def get_osengine(self, debug = False):        
        if debug or CharmeMiddleware.__osEngine is None:
            CharmeMiddleware.__initOsEngine()
        return CharmeMiddleware.__osEngine
      
    def process_request(self, request):
        if request.method == 'OPTIONS':
            return HttpResponse(status=200)             
         
        if CharmeMiddleware.get_store() is None:
            try:
                self.__initStore()
            except AttributeError, e:
                messages.add_message(request, messages.ERROR, e)
                messages.add_message(request, messages.INFO, 'Missing configuration')
                return mm_render_to_response_error(request, '503.html', 503)

        if CharmeMiddleware.get_osengine() is None:
            try:
                self.__initOsEngine()
            except Exception, e:
                messages.add_message(request, messages.ERROR, e)
                messages.add_message(request, messages.INFO, 'Missing configuration. \
Cannot initialize OpenSearch Engine')
                return mm_render_to_response_error(request, '503.html', 503)

        self._validate_request(request)

    def process_response(self, request, response):
        response['Access-Control-Allow-Origin'] = \
            request.META.get('HTTP_ORIGIN', 
                             'http://localhost:8000')
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Expose-Headers'] = 'Location, Content-Type, Content-Length';
        
        if request.method == 'OPTIONS':
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'               
            response['Access-Control-Allow-Headers'] = 'X-Requested-With, x-requested-with, Content-Type, Content-Length'
            #response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', 'http://localhost:8000')
            response['Access-Control-Max-Age'] = 10
            response['Content-Type'] = "text/plain"
            return response
        return response
    
    def process_exception(self, request, exception):
        print 'ERROR!'

    def _get_user_roles(self, user):
        #user.roles = contact_role_server
        #return user
        pass

    def _is_authenticated(self, request):
        pass

    def _validate_request(self, request):
        user = self._is_authenticated(request)
        #Here should compare:
        # - the request method ('get/put/post/delete')
        # - the request resource ('URI')
        pass