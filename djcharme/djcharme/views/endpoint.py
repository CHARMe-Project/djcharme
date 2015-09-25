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

Created on 14 May 2013

@author: mnagni
'''
import logging

from django.http.response import HttpResponseRedirectBase, HttpResponse
from rdflib.graph import ConjunctiveGraph
from rdflib.term import URIRef

from djcharme.charme_middleware import CharmeMiddleware
from djcharme.node.actions import  insert_rdf, generate_graph, rdf_format_from_mime
from djcharme.views import isGET, isPOST, isPUT, isDELETE, isHEAD, isPATCH, \
    content_type


LOGGING = logging.getLogger(__name__)


class HttpResponseSeeOther(HttpResponseRedirectBase):
    status_code = 303


def endpoint(request):
    if isGET(request):
        return processGET(request)
    if isPUT(request):
        return processPUT(request)
    if isDELETE(request):
        return processDELETE(request)
    if isPOST(request):
        return processPOST(request)
    if isHEAD(request):
        return processHEAD(request)
    if isPATCH(request):
        return processPATCH(request)


def get_graph_from_request(request):
    graph = request.GET.get('graph', 'default')

    if graph == 'default':
        graph = None
    return graph


def processGET(request):
    '''
        Returns an httplib.HTTPRequest
    '''
    return processHEAD(request, True)


def processPUT(request):
    graph = get_graph_from_request(request)
    payload = request.body

    conjunctive_graph = None
    query_object = None
    if graph is None:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
        query_object = '''
            DROP SILENT DEFAULT;
            '''
        query_object = ''
    else:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
        query_object = '''
            DROP SILENT GRAPH <%s>;
            '''
        query_object = query_object % (graph)
    conjunctive_graph.update(query_object)
    insert_rdf(payload,
               content_type(request),
               request.user,
               request.client,
               graph)

    return HttpResponse(status=204)


def processDELETE(request):
    graph = get_graph_from_request(request)

    conjunctive_graph = None
    query_object = None
    if graph is None:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
        query_object = '''
            DROP DEFAULT;
            '''
        query_object = ''
    else:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
        query_object = '''
            DROP GRAPH <%s>;
            '''
        query_object = query_object % (graph)
    conjunctive_graph.update(query_object)

    return HttpResponse(status=204)


def processPOST(request):
    graph = get_graph_from_request(request)
    payload = request.body
    insert_rdf(payload,
               content_type(request),
               request.user,
               request.client,
               graph)

    return HttpResponse(status=204)


def processHEAD(request, return_content=False):
    '''
        Returns an httplib.HTTPRequest
    '''
    graph = get_graph_from_request(request)
    accept = _validate_mime_format(request, 'application/rdf+xml')

    if accept == None:
        return HttpResponse(status=406)

    conjunctive_graph = None
    if graph is None:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
    else:
        conjunctive_graph = generate_graph(CharmeMiddleware.get_store(),
                                           URIRef(graph))

    content = conjunctive_graph.serialize(format=accept)

    if return_content:
        return HttpResponse(content=content)
    return HttpResponse()


def processPATCH(request):
    return HttpResponse(status=501)


def _validate_mime_format(request, default=None):
    """
    Returns the first valid mimetype as mapped as rdf format
    """
    req_formats = request.META.get('HTTP_ACCEPT', default)
    req_formats = req_formats.split(',')
    for req_format in req_formats:
        if rdf_format_from_mime(req_format) != None:
            return req_format
    if ((len(req_formats) == 0) or
        (len(req_formats) == 1 and req_formats[0] == '*/*')):
        return default
    return None
