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

Created on 14 May 2013

@author: mnagni
'''
import httplib
import json
import logging
import urllib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import (HttpResponseRedirectBase,
                                  HttpResponseNotFound, HttpResponse)
from rdflib.graph import ConjunctiveGraph
from rdflib.term import URIRef

from djcharme import mm_render_to_response, mm_render_to_response_error, \
    settings
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.exception import NotFoundError
from djcharme.exception import SecurityError
from djcharme.exception import SerializeError, StoreConnectionError
from djcharme.exception import UserError
from djcharme.node.actions import  insert_rdf, find_resource_by_id, \
    _collect_annotations, change_annotation_state, find_annotation_graph, \
    generate_graph, rdf_format_from_mime
from djcharme.node.constants import OA, FORMAT_MAP, RESOURCE, SUBMITTED
from djcharme.views import isGET, isPOST, isPUT, isDELETE, \
    isHEAD, isPATCH, content_type


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


def _get_connection():
    '''
        Returns an httplib.HTTPConnection instance pointing to
        settings.SPARQL_HOST_NAME
    '''
    return httplib.HTTPConnection(getattr(settings, 'SPARQL_HOST_NAME'),
                                  port=getattr(settings, 'SPARQL_PORT'))


def _submit_get(graph, accept):
    headers = {"Accept": accept}
    params = urllib.urlencode({'graph': graph})
    conn = _get_connection()
    conn.request('GET', getattr(settings, 'GRAPH_STORE_RW_PATH'),
                 params, headers)
    response = conn.getresponse()
    return response


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


def __serialize(graph, req_format='application/rdf+xml'):
    '''
        Serializes a graph according to the required format
    '''
    if req_format == 'application/ld+json':
        req_format = 'json-ld'
    return graph.serialize(format=req_format)


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


def _validate_format(request):
    '''
        Returns the mimetype of the required format as mapped by rdflib
        return: String - an allowed rdflib mimetype
    '''
    req_format = None
    if isGET(request):
        req_format = FORMAT_MAP.get(request.GET.get('format', None))
    if isPOST(request):
        req_format = request.environ.get('CONTENT_TYPE', None)

    if req_format:
        if req_format not in FORMAT_MAP.values():
            raise SerializeError("Cannot generate the required format %s "
                                 % req_format)
    return req_format


@login_required
def index(request, graph='stable'):
    '''
        Returns a tabular view of the stored annotations.
        *request: HTTPRequest - the client request
        *graph: String -  the required named graph
        TDB - In a future implementation this actions should be supported by an
        OpenSearch implementation
    '''
    tmp_g = None
    try:
        tmp_g = _collect_annotations(graph)
    except StoreConnectionError as ex:
        LOGGING.error("Internal error. " + str(ex))
        messages.add_message(request, messages.ERROR, ex)
        return mm_render_to_response_error(request, '503.html', 503)

    req_format = _validate_format(request)

    if req_format:
        LOGGING.debug("Annotations %s", str(__serialize
                                            (tmp_g, req_format=req_format)))
        return HttpResponse(__serialize(tmp_g, req_format=req_format))

    states = {}
    LOGGING.debug("Annotations %s", str(tmp_g.serialize()))
    for subject, pred, obj in tmp_g.triples((None, None, OA['Annotation'])):
        states[subject] = find_annotation_graph(subject)

    context = {'results': tmp_g.serialize(), 'states': json.dumps(states)}
    return mm_render_to_response(request, context, 'viewer.html')


def insert(request):
    '''
        Inserts in the triplestore a new annotation under the "SUBMITTED"
        graph
    '''
    req_format = _validate_format(request)

    if request.method == 'POST':
        triples = request.body
        anno_uri = insert_rdf(triples, req_format, request.user, request.client,
                              graph=SUBMITTED)
        return HttpResponse(anno_uri)


def advance_status(request):
    '''
        Advance the status of an annotation
    '''
    if isPOST(request) and 'application/ld+json' in content_type(request):
        params = json.loads(request.body)
        LOGGING.info("advancing %s to state:%s", str(params.get('annotation')),
                     str(params.get('toState')))
        try:
            tmp_g = change_annotation_state(params.get('annotation'),
                                            params.get('toState'), request)
        except NotFoundError as ex:
            messages.add_message(request, messages.ERROR, str(ex))
            return mm_render_to_response_error(request, '404.html', 404)
        except SecurityError as ex:
            messages.add_message(request, messages.ERROR, str(ex))
            return mm_render_to_response_error(request, '403.html', 403)
        except UserError as ex:
            messages.add_message(request, messages.ERROR, str(ex))
            return mm_render_to_response_error(request, '400.html', 400)
        if tmp_g == None:
            return HttpResponse()
        else:
            return HttpResponse(tmp_g.serialize())
    elif not isPOST(request):
        messages.add_message(request, messages.ERROR,
                             "Message must be a POST")
        return mm_render_to_response_error(request, '405.html', 405)
    else:
        messages.add_message(request, messages.ERROR,
                             "Message must contain application/ld+json")
        return mm_render_to_response_error(request, '400.html', 400)


def process_resource(request, resource_id):
    if _validate_mime_format(request):
        LOGGING.info("Redirecting to /%s/%s", str(RESOURCE), str(resource_id))
        return HttpResponseSeeOther('/%s/%s' % (RESOURCE, resource_id))
    if 'text/html' in request.META.get('HTTP_ACCEPT', None):
        LOGGING.info("Redirecting to /page/%s", str(resource_id))
        return HttpResponseSeeOther('/page/%s' % resource_id)
    return HttpResponseNotFound()


def process_data(request, resource_id):
    req_format = _validate_mime_format(request)
    if req_format is None:
        return process_resource(request, resource_id)

    tmp_g = find_resource_by_id(resource_id)
    return HttpResponse(tmp_g.serialize(format=req_format),
                        mimetype=request.META.get('HTTP_ACCEPT'))


def process_page(request, resource_id=None):
    if 'text/html' not in request.META.get('HTTP_ACCEPT', None):
        process_resource(request, resource_id)

    tmp_g = find_resource_by_id(resource_id)
    context = {'results': tmp_g.serialize()}
    return mm_render_to_response(request, context, 'viewer.html')
