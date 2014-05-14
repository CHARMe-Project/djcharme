'''
BSD Licence
Copyright (c) 2012, Science & Technology Facilities Council (STFC)
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
Created on 1 Nov 2011

@author: Maurizio Nagni
'''
import logging
import socket

from django.contrib import messages
from django.contrib.messages.api import MessageFailure
from django.core.context_processors import csrf
from django.http.response import HttpResponse
from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe
from rdflib.plugin import PluginException

from djcharme import mm_render_to_response_error
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.node.actions import FORMAT_MAP


hostURL = 'http://localhost:8000'

LOGGING = logging.getLogger(__name__)

def _build_host_url(request):
    hostname = socket.getfqdn()
    if request.META['SERVER_PORT'] != str(80):
        hostname = "%s:%s" % (hostname, request.META['SERVER_PORT'])
    return 'http://%s' % (hostname)

'''
def _build_host_url(request):
    root = ''
    if non_root_url != 'PROJECT_NAME_PAR' :
        root = non_root_url
    if 'localhost' in request.get_host():
        return 'http://%s' % (request.get_host())

    if request.is_secure():
        return 'https://%s/%s' % (request.get_host(), root)
    else:
        return 'http://%s/%s' % (request.get_host(), root)
'''

def get_home(request):
    context = {}
    context['hostURL'] = _build_host_url(request)
    return _dispatch_response(request, 'homeTemplate', context)


def get_description(request, collection_guid=None,
                   observation_guid=None,
                   result_guid=None):
    host_url = _build_host_url(request)
    ospath = _build_description_ospath(host_url, collection_guid,
                                       observation_guid, result_guid)
    response = CharmeMiddleware.get_osengine().get_description(ospath)
    context = {}
    context['response'] = mark_safe(response)
    return _dispatch_response(request, 'responseTemplate.html', context)

def do_search(request, iformat):
    host_url = _build_host_url(request)
    context = CharmeMiddleware.get_osengine().create_query_dictionary()
    if request.GET is not None:
        for param in request.GET.iteritems():
            context[param[0]] = param[1]

    context.update(context)
    try:         
        response = CharmeMiddleware.get_osengine().do_search(host_url,
                                                         iformat, context)
        return HttpResponse(response, mimetype=FORMAT_MAP.get(iformat))
    except Exception as e:
        try:
            messages.add_message(request, messages.ERROR, e)
        except PluginException as e:
            LOGGING.error(str(e))
        except MessageFailure as e:
            LOGGING.error(str(e))
        return mm_render_to_response_error(request, '503.html', 503)

def _build_description_ospath(hostURL, collection_guid=None,
                              observation_guid=None, result_guid=None):
    ospath = "%s/search/" % (hostURL)
    if collection_guid:
        ospath = "%s%s/" % (ospath, collection_guid)
    if observation_guid:
        ospath = "%s%s/" % (ospath, observation_guid)
    if result_guid:
        ospath = "%s%s/" % (ospath, result_guid)
    return ospath

def _dispatch_response(request, template, context):
    context.update(csrf(request))
    return render_to_response(template, context)
