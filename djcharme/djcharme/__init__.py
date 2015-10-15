'''
BSD Licence
Copyright (c) 2015, Science & Technology Facilities Council (STFC)
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

'''
__version__ = '0.8.1'


import os

from django.conf import settings
from django.core.context_processors import csrf
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from django.shortcuts import render_to_response, render
from django.template.context import RequestContext


LOAD_SAMPLE = 'LOAD_SAMPLE'
HTTP_PROXY = 'HTTP_PROXY'
HTTP_PROXY_PORT = 'HTTP_PROXY_PORT'


def get_resource(file_name):
    return os.path.join(__path__[0], 'resources', file_name)


def mm_render_to_response(request, context, page_to_render):
    """
    Exploits a 'render_to_response' action. The advantage of this method
    is to contains a number of operations that are expected to be  called
    for each page rendering, for example passing the application version number

    **Parameters**
        * HttpRequest_ **request**
            a django HttpRequest instance
        * `dict` **context**
            a dictionary where to pass parameter to the rendering function
        * `string` **page_to_render**
            the html page to render
    """
    if context is None or not isinstance(context, dict):
        raise Exception("Cannot render an empty context")

    # context['version'] = assemble_version()
    context.update(csrf(request))
    rcontext = RequestContext(request, context)
    return render_to_response(page_to_render, rcontext)


def mm_render_to_response_error(request, page_to_render, status):
    """
    Exploits a 'render_to_response' action. The advantage of this method
    is to contains a number of operations that are expected to be  called
    for each page rendering, for example passing the application version number

    **Parameters**
        * HttpRequest_ **request**
            a django HttpRequest instance
        * `dict` **context**
            a dictionary where to pass parameter to the rendering function
        * `string` **page_to_render**
            the html page to render
    """
    context = {}
    context.update(csrf(request))
    rcontext = RequestContext(request, context)
    return render(request, page_to_render, context_instance=rcontext,
                  status=status)
