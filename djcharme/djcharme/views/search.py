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
from djcharme.node.constants import FORMAT_MAP
from djcharme.node.search import get_multi_value_parameter_names


LOGGING = logging.getLogger(__name__)


def _build_host_url(request):
    hostname = socket.getfqdn()
    if (request.META['SERVER_PORT'] != str(80)
        and request.META['SERVER_PORT'] != str(443)):
        hostname = "%s:%s" % (hostname, request.META['SERVER_PORT'])
    if request.is_secure():
        return 'https://%s' % (hostname)
    else:
        return 'http://%s' % (hostname)


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
    context = _update_context(request)
    try:
        response = CharmeMiddleware.get_osengine().do_search(host_url,
                                                             iformat, context)
        return HttpResponse(response, mimetype=FORMAT_MAP.get(iformat))
    except Exception as ex:
        try:
            messages.add_message(request, messages.ERROR, ex)
            LOGGING.error(str(ex))
        except PluginException as ex:
            LOGGING.error(str(ex))
        except MessageFailure as ex:
            LOGGING.error(str(ex))
        return mm_render_to_response_error(request, '503.html', 503)


def do_suggest(request, iformat):
    host_url = _build_host_url(request)
    context = _update_context(request)
    try:
        # TODO change when ceda_markup has been updated to accept do_suggest
        context['suggest'] = True
        response = CharmeMiddleware.get_osengine().do_search(host_url,
                                                             iformat, context)
        return HttpResponse(response, mimetype=FORMAT_MAP.get(iformat))
    except Exception as ex:
        try:
            messages.add_message(request, messages.ERROR, ex)
            LOGGING.error(str(ex))
        except PluginException as ex:
            LOGGING.error(str(ex))
        except MessageFailure as ex:
            LOGGING.error(str(ex))
        return mm_render_to_response_error(request, '503.html', 503)


def _update_context(request):
    context = CharmeMiddleware.get_osengine().create_query_dictionary()
    search_parameter_names = get_multi_value_parameter_names()
    if request.GET is not None:
        # TODO remove next two lines
        for param in request.GET.iteritems():
            context[param[0]] = param[1]
            # TODO use list when I can work out how to sort out the response
#         for key in request.GET.keys():
#             if search_parameter_names.count(key) > 0:
#                 context[key] = request.GET.getlist(key)
#             else:
#                 context[key] = request.GET.get(key)
    context.update(context)
    return context


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
